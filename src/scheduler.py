#!/usr/bin/env python3
""" Scheduler """

import os
import glob
import time
import queue
import threading

from src.job import Job
from src.trace import Trace, TraceRecord
from src.result import Result
from src.output import Output

class Scheduler:
    """
    Creates benchmark jobs and runs jobs (in parallel)
    """

    def __init__(self, runner, result_path, configurations):
        self.runner = runner
        self.result_path = result_path
        self.configurations = configurations
        self.time_start = time.time()
        self.jobs = queue.Queue()
        self.trace = Trace()
        self.output = Output()


    def _model_files(self, model_path):
        pattern = os.path.join(model_path, "*." + self.runner.modelfile_ext)
        return sorted(glob.glob(pattern))


    @staticmethod
    def _configuration_name(configuration):
        name = ''
        for i, (_, option) in enumerate(configuration):
            if i > 0:
                name += '_'
            name += str(option)
        return name


    def num_jobs(self):
        """
        Returns the number of jobs currently in the job pool
        """
        return self.jobs.qsize()


    def create(self, model_path, max_jobs=10000000, max_time=60, kill_time=30):
        """
        Creates benchmark jobs

        Arguments
        ---------
        model_path: str
            Path to model instances
        max_jobs: int
            Max allowed jobs
        max_time: int
            Max allowed time per job
        kill_time: int
            Time (+max_time) after which a process should be killed
        """

        for conf in self.configurations:
            conf_name = self._configuration_name(conf)
            for model in self._model_files(model_path):
                if self.num_jobs() + 1 > max_jobs:
                    return
                modelname = os.path.splitext(os.path.basename(model))[0]
                workdir = os.path.join(self.result_path, conf_name, modelname)
                job = Job(modelname, workdir, model, conf, max_time, kill_time)
                self.jobs.put(job)


    def run(self, n_threads=1, max_duration=10000000):
        """
        Starts the benchmark

        Arguments
        ---------
        n_threads: int
            Number of threads to run jobs in parallel
        max_duration: int
            Max allowed total duration of benchmark
        """

        for i in range(n_threads):
            self.jobs.put(None)

        # run jobs
        if n_threads == 1:
            self._run_thread(0, max_duration)
        else:
            threads = []
            for i in range(n_threads):
                threads.append(threading.Thread(target=self._run_thread, args=(i, max_duration)))
                threads[-1].start()

            for i in range(n_threads):
                threads[i].join()

        # write results
        for conf in self.configurations:
            conf_name = self._configuration_name(conf)
            self.trace.write(os.path.join(self.result_path, conf_name, 'trace.trc'))


    def _duration(self):
        return time.time() - self.time_start


    def _run_thread(self, thread_id, max_duration):
        while True:
            job = self.jobs.get()
            if job is None:
                break

            if job.init_workdir() and self._duration() <= max_duration:
                result = self.runner.run(job)
                self.trace.append(result.trace)
            else:
                trace = TraceRecord()
                trace.load_trc(os.path.join(job.workdir, 'trace.trc'))
                result = Result(trace, "", "")
                self.trace.append(trace)

            self.output.print(job, result, self._duration(), self.num_jobs(), thread_id)
