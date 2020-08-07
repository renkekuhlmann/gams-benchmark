#!/usr/bin/env python3
""" Runner """

from trace import TraceRecord
from result import Result

class Runner:
    """
    Template for running a GAMS job through an interface
    """

    def __init__(self):
        self.name = ''
        self.version_gams = ''
        self.version_interface = ''
        self.modelfile_ext = ''


    def command(self, job):
        """
        Runs a GAMS job using the command line

        Arguments
        ---------
        job : Job
            Benchmark job
        """
        # pylint: disable=unused-argument,no-self-use
        return ['NOT AVAILABLE']


    def run(self, job):
        """
        Runs a GAMS job using the command line. Returns result.

        Arguments
        ---------
        job : Job
            Benchmark job
        """
        # pylint: disable=unused-argument,no-self-use
        return Result(TraceRecord(job.filename()), "", "")
