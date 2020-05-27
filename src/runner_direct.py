#!/usr/bin/env python3

import os
import re
import time
import subprocess

from src.runner import Runner
from src.trace import TraceRecord

class RunnerDirect(Runner):

    def __init__(self, sysdir):
        Runner.__init__(self)
        self.sysdir = sysdir
        self.name = 'direct'
        self.modelfile_ext = 'gms'
        self.version_gams = self.get_version(sysdir)


    @staticmethod
    def get_version(sysdir):
        cmd = os.path.join(sysdir, 'gams')
        process = subprocess.Popen([cmd, 'audit', 'lo=3'], stdout=subprocess.PIPE)
        stdout = str(process.communicate())
        return re.findall("[0-9]+.[0-9]+.[0-9]+", stdout)[0]


    def command(self, workdir, name, conf, time_limit=60, time_kill=30):
        cmd = ['timeout', '%d' % (time_limit + time_kill),
               os.path.join(self.sysdir, 'gams'), os.path.join(workdir, name + '.gms'),
               'lo=2', 'al=0', 'ao=0', 'curdir=%s' % workdir, 'trace=trace.trc',
               'traceOpt=5', 'reslim=%d' % time_limit, 'solprint=off', 'solvelink=5']
        for (key, value) in conf:
            if key == 'id':
                continue
            cmd.append(key + "=" + value)
        return cmd


    def run(self, workdir, name, conf, time_limit=60, time_kill=30):
        cmd = self.command(workdir, name, conf, time_limit, time_kill)

        # solve
        time_interface = time.time()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env={'LD_LIBRARY_PATH': self.sysdir})
        stdout, stderr = process.communicate()
        time_interface = time.time() - time_interface
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

        trc.record['ETInterface'] = time_interface
        if trc.record['SolverTime'] is not None:
            trc.record['ETIntOverhead'] = trc.record['ETInterface'] - trc.record['SolverTime']
        trc.write(os.path.join(workdir, "trace.trc"))

        return trc, stdout, stderr
