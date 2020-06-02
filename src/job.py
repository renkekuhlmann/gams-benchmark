#!/usr/bin/env python3
""" Job """

import os
import shutil

class Job:
    """
    A Benchmark Job
    Holds GAMS options and information about model file and working directory
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, name, workdir, model_file, configuration, max_time, kill_time):
        # pylint: disable=too-many-arguments
        self.name = name
        self.configuration = configuration
        self.workdir = os.path.abspath(workdir)
        self.model_file = model_file
        self.max_time = max_time
        self.kill_time = kill_time


    def filename(self):
        """
        Returns file name of job
        """
        return os.path.basename(self.model_file)


    def init_workdir(self):
        """
        Creating the working directory for the job and copying model file
        """

        if os.path.exists(self.workdir):
            if not os.path.exists(os.path.join(self.workdir, 'trace.trc')):
                shutil.rmtree(self.workdir)
            else:
                return False
        os.makedirs(self.workdir)
        model_file = os.path.basename(self.model_file)
        shutil.copyfile(self.model_file, os.path.join(self.workdir, model_file))
        return True
