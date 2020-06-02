#!/usr/bin/env python3
""" RunnerPyomo """

import os
import shutil
import re
import subprocess
import pickle

import pyomo.environ as pyo
import pyomo.version as pyover

from src.runner import Runner
from src.trace import TraceRecord
from src.result import Result

class RunnerPyomo(Runner):
    """
    Running a GAMS job through Pyomo
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        Runner.__init__(self)
        self.name = 'pyomo'
        self.modelfile_ext = 'py'
        self._get_version()


    def _get_version(self):
        # dummy problem
        model = pyo.ConcreteModel()
        model.x = pyo.Var(within=pyo.Reals, bounds=(0, 1))
        model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)
        opt = pyo.SolverFactory('gams')
        results = opt.solve(model)
        version = re.findall("[0-9]+,[ 0-9]+,[ 0-9]+,[ 0-9]+", results.solver.name)
        if not version:
            raise Exception("Can't find GAMS version within pyomo")
        version = version[0].split(', ')[0:3]

        # versions
        self.version_interface = "%d.%d.%d" % (pyover.version_info[0:3])
        self.version_gams = "%s.%s.%s" % (version[0], version[1], version[2])


    def _program(self, job):
        # pylint: disable=no-self-use

        # gams options
        pyconf = 'opt.options["add_options"] = []\n'
        for (key, value) in job.configuration:
            if key == 'id':
                continue
            if key.lower() == 'nodlim':
                pyconf += 'opt.options["add_options"].append("GAMS_MODEL.%s=%s;")\n' % (key, value)
            else:
                pyconf += 'opt.options["add_options"].append("option %s=%s;")\n' % (key, value)

        # pyomo program
        pyprog = """
import os
import time
import pickle
import pyomo.environ as pyo
from pyomo.opt import SolverFactory

opt = pyo.SolverFactory('gams')
opt.options["keepfiles"] = True
%s
opt.options["add_options"].append("option reslim=%d;")

# load pyomo problem
m = getattr(__import__('%s', fromlist=["m"]), "m")

# solve
time_used = time.time()
results = opt.solve(m)
time_used = time.time() - time_used

# store
with open(os.path.join('%s', 'pyomo_result.pkl'), 'wb') as f:
    pickle.dump([results, time_used], f)
        """ % (pyconf, job.max_time, job.name, job.workdir)

        prog = 'pyomo_' + job.name + '.py'
        with open(os.path.join(job.workdir, prog), 'w') as fio:
            fio.write(pyprog)
        return prog, pyprog


    def run(self, job):
        """
        Runs a GAMS job using the command line. Returns result.

        Arguments
        ---------
        job : Job
            Benchmark job
        """

        # solve
        prog, _ = self._program(job)
        progpath = os.path.join(job.workdir, prog)
        cmd = ['timeout', '%d' % (job.max_time + job.kill_time), 'python', progpath]
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
            with open(os.path.join(job.workdir, 'pyomo_result.pkl'), 'rb') as fio:
                results, trc.record['ETInterface'] = pickle.load(fio)

            stats = results.problem
            tmpdir = os.path.dirname(stats.name)
            trcfile = os.path.join(tmpdir, 'trace.trc')
            # parse trace file
            if os.path.exists(trcfile):
                trc.load_trc(trcfile)
                trc.record['InputFileName'] = job.filename()
            # parse lst and pyomo result file
            else:
                trc.load_lst(os.path.join(tmpdir, 'output.lst'))
                shutil.rmtree(tmpdir)

                trc.record['NumberOfEquations'] = stats.number_of_constraints
                trc.record['NumberOfVariables'] = stats.number_of_variables
                trc.record['NumberOfDiscreteVariables'] = stats.number_of_integer_variables
                trc.record['NumberOfNonZeros'] = stats.number_of_nonzeros
                if trc.record['Direction'] == 0:
                    trc.record['ObjectiveValue'] = stats.upper_bound
                    trc.record['ObjectiveValueEstimate'] = stats.lower_bound
                else:
                    trc.record['ObjectiveValue'] = stats.lower_bound
                    trc.record['ObjectiveValueEstimate'] = stats.upper_bound

        except IOError:
            trc.record['SolverStatus'] = 13
            trc.record['ModelStatus'] = 12

        # compute interface overhead
        if trc.record['SolverTime'] is not None and trc.record['ETInterface'] is not None:
            trc.record['ETInterfaceOverhead'] = trc.record['ETInterface'] - trc.record['SolverTime']

        # write trace file
        trc.write(os.path.join(job.workdir, 'trace.trc'))

        return Result(trc, stdout, stderr)
