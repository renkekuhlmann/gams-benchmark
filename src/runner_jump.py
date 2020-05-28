#!/usr/bin/env python3
""" RunnerJump """

import os
import re
import subprocess
from multiprocessing import Process

from src.runner import Runner
from src.runner_direct import RunnerDirect
from src.trace import TraceRecord

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


    def _program(self, workdir, name, conf, time_limit):
        # gams options
        jlconf = ""
        for (key, value) in conf:
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
        """ % (workdir, name, self.sysdir, workdir, jlconf, time_limit, workdir)

        prog = 'jump_' + name + '.jl'
        with open(os.path.join(workdir, prog), 'w') as fio:
            fio.write(jlprog)
        return prog, jlprog


    def run(self, workdir, name, conf, time_limit=60, time_kill=30):
        """
        Runs a GAMS job through JuMP

        Arguments
        ---------
        workdir: string
            Working directory for job
        name: string
            Name of job (job file without extension)
        conf: list
            GAMS options
        time_limit: int
            Time limit for GAMS job
        time_kill: int
            Additional time to time_limit till a process should be killed

        Returns
        -------
        TraceRecord: job results
        str: standard output of job
        str: standard error of job
        """
        # pylint: disable=too-many-arguments,too-many-locals

        # solve
        prog, jlprog = self._program(workdir, name, conf, time_limit)
        if self.use_pyjulia:
            process = Process(target=self._run_julia(jlprog))
            process.start()
            process.join(timeout=time_limit + time_kill)
            process.terminate()
            stdout = ""
            stderr = ""
        else:
            cmd = ['timeout', '%d' % (time_limit + time_kill), 'julia', os.path.join(workdir, prog)]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            stdout = stdout.decode("utf-8")
            stderr = stderr.decode("utf-8")

        # store stdout / stderr
        with open(os.path.join(workdir, 'stdout.txt'), 'w') as fio:
            fio.write(stdout)
        with open(os.path.join(workdir, 'stderr.txt'), 'w') as fio:
            fio.write(stderr)

        # process solution
        trc = TraceRecord()
        try:
            trc.load_trc(os.path.join(workdir, "trace.trc"))
        except FileNotFoundError:
            trc.record['SolverStatus'] = 13
            trc.record['ModelStatus'] = 12

        trc.record['InputFileName'] = name + '.jl'

        # process solution (jump result file)
        result_file = os.path.join(workdir, 'jump_results.txt')
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
        trc.write(os.path.join(workdir, 'trace.trc'))

        return trc, stdout, stderr
