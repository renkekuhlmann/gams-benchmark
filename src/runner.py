#!/usr/bin/env python3

class Runner:

    def __init__(self):
        self.name = ''
        self.version_gams = ''
        self.version_interface = ''
        self.modelfile_ext = ''


    def command(self, workdir, name, solver, time_limit=60, time_kill=30, time_interface=False):
        # pylint: disable=too-many-arguments, unused-argument
        return ['NOT AVAILABLE']


    def run(self, workdir, name, solver, time_limit=60, time_kill=30, time_interface=False):
        # pylint: disable=too-many-arguments, unused-argument
        return 0, 0, 0.0
