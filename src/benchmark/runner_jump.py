#!/usr/bin/env python3
""" RunnerJump """

import os
import re
import subprocess
from multiprocessing import Process

from runner import Runner
from runner_direct import RunnerDirect
from trace import TraceRecord
from result import Result

class RunnerJump(Runner):
    """
    Running a GAMS job through JuMP
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, sysdir, use_pyjulia=False):
        Runner.__init__(self)
        self.name = 'jump'
        self.modelfile_ext = 'jl'
        self.sysdir = sysdir
        self._get_version()
        self.use_pyjulia = use_pyjulia
        if self.use_pyjulia:
            self._init_julia()


    def _get_version(self):
        cmd = ['julia', '-e', 'using Pkg; Pkg.status("JuMP")']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        stdout = stdout.decode("utf-8")
        version = re.findall("[0-9]+.[ 0-9]+.[ 0-9]+", stdout)
        if len(version) >= 1:
            self.version_interface = version[0]
        self.version_gams = RunnerDirect.get_version(self.sysdir)


    @staticmethod
    def _init_julia():
        # pylint: disable=import-outside-toplevel
        print('Init Julia Environment. This can take some time...')
        print('Julia...', end='', flush=True)
        from julia import Julia
        Julia(compiled_modules=False)
        from julia import Main
        print('ok! JuMP...', end='', flush=True)
        Main.using('JuMP')
        print('ok! GAMS...', end='', flush=True)
        Main.using('GAMS')
        print('ok!')


    @staticmethod
    def _run_julia(jlprog):
        # pylint: disable=import-outside-toplevel
        from julia import Main, JuliaError
        try:
            Main.eval(jlprog)
        except JuliaError:
            pass


    def _program(self, job):
        # gams options
        jlconf = ""
        for (key, value) in job.configuration:
            if key == 'id':
                continue
            jlconf += 'set_optimizer_attribute(m, "%s", "%s")\n' % (key, value)

        # julia program
        jlprog = """
using JuMP
using GAMS

include(joinpath("%s", "%s.jl"))

JuMP.set_optimizer(m, GAMS.Optimizer)
set_optimizer_attribute(m, GAMS.SysDir(), "%s")
set_optimizer_attribute(m, GAMS.WorkDir(), "%s")
set_optimizer_attribute(m, MOI.Silent(), true)
%s
set_optimizer_attribute(m, MOI.TimeLimitSec(), 1)
JuMP.optimize!(m)

set_optimizer_attribute(m, GAMS.Trace(), "trace.trc")
set_optimizer_attribute(m, GAMS.TraceOpt(), 5)
set_optimizer_attribute(m, MOI.TimeLimitSec(), %d)
time_used = @elapsed JuMP.optimize!(m)

open(joinpath("%s", "jump_results.txt"), "w") do io
    write(io, "time_used " * string(time_used) * "\n")
end
        """ % (job.workdir, job.name, self.sysdir, job.workdir, jlconf,
               job.max_time, job.workdir)

        prog = 'jump_' + job.name + '.jl'
        with open(os.path.join(job.workdir, prog), 'w') as fio:
            fio.write(jlprog)
        return prog, jlprog


    def run(self, job):
        """
        Runs a GAMS job using the command line. Returns result.

        Arguments
        ---------
        job : Job
            Benchmark job
        """
        # pylint: disable=too-many-locals

        # solve
        prog, jlprog = self._program(job)
        if self.use_pyjulia:
            process = Process(target=self._run_julia(jlprog))
            process.start()
            process.join(timeout=job.max_time + job.kill_time)
            process.terminate()
            stdout = ""
            stderr = ""
        else:
            progpath = os.path.join(job.workdir, prog)
            cmd = ['timeout', '%d' % (job.max_time + job.kill_time), 'julia', progpath]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            stdout = stdout.decode("utf-8")
            stderr = stderr.decode("utf-8")

        # store stdout / stderr
        with open(os.path.join(job.workdir, 'stdout.txt'), 'w') as fio:
            fio.write(stdout)
        with open(os.path.join(job.workdir, 'stderr.txt'), 'w') as fio:
            fio.write(stderr)

        # process solution
        trc = TraceRecord(job.filename())
        try:
            trc.load_trc(os.path.join(job.workdir, "trace.trc"))
            trc.record['InputFileName'] = job.filename()
        except FileNotFoundError:
            trc.record['SolverStatus'] = 13
            trc.record['ModelStatus'] = 12

        # process solution (jump result file)
        result_file = os.path.join(job.workdir, 'jump_results.txt')
        if os.path.exists(result_file):
            with open(result_file, 'r') as fio:
                lines = fio.readlines()
                for line in lines:
                    key, value = line.replace("\n", "").split(" ")
                    if key == "time_used":
                        trc.record['ETInterface'] = float(value)

        # compute interface overhead
        if trc.record['SolverTime'] is not None and trc.record['ETInterface'] is not None:
            trc.record['ETInterfaceOverhead'] = trc.record['ETInterface'] - trc.record['SolverTime']

        # write trace file
        trc.write(os.path.join(job.workdir, 'trace.trc'))

        return Result(trc, stdout, stderr)
