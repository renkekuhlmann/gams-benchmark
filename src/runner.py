#!/usr/bin/env python3
""" Runner """

from src.trace import TraceRecord

class Runner:
    """
    Template for running a GAMS job through an interface
    """

    def __init__(self):
        self.name = ''
        self.version_gams = ''
        self.version_interface = ''
        self.modelfile_ext = ''


    def command(self, workdir, name, conf, time_limit=60, time_kill=30):
        """
        GAMS command for given job

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
        """
        # pylint: disable=no-self-use,too-many-arguments,unused-argument
        return ['NOT AVAILABLE']


    def run(self, workdir, name, conf, time_limit=60, time_kill=30):
        """
        Runs a GAMS job

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
        # pylint: disable=no-self-use,too-many-arguments,unused-argument
        return TraceRecord(), "", ""
