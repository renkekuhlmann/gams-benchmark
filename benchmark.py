#!/usr/bin/env python3
"""
GAMS Benchmark

Author: Renke Kuhlmann, GAMS Software GmbH
"""

import argparse
import os
import glob
import threading
import queue
import time
import sys
from shutil import copyfile

from src.trace import Trace

def _args():
    parser = argparse.ArgumentParser(description='Benchmark GAMS.')
    parser.add_argument('--testset', type=str, default='minlplib',
                        choices=['minlplib', 'princetonlib'],
                        help='Name of testset (default: minlplib)')
    parser.add_argument('--result', type=str, default='latest',
                        help='Result directory (default: latest)')
    parser.add_argument('--gams', type=str, default='/opt/gams',
                        help='Path to GAMS (default: /opt/gams)')
    parser.add_argument('--gamsopt', type=str, default='',
                        help='GAMS Options, format: gamsopt1=value1,gamsopt2=value2...')
    parser.add_argument('--max_time', type=int, default='60',
                        help='Max time for solve (default: 60)')
    parser.add_argument('--kill_time', type=int, default='30',
                        help='Time added to max_time before process is killed (default: 30)')
    parser.add_argument('--threads', type=int, default='1',
                        help='Threads used to solve <n> models in parallel (default: 1)')
    parser.add_argument('--jobs_max', type=int, default=10000000,
                        help='Max jobs')
    parser.add_argument('--jobs_max_time', type=int, default=10000000,
                        help='Max jobs')
    parser.add_argument('--interface', type=str, default='direct',
                        choices=['direct', 'pyomo', 'jump'],
                        help='Call GAMS through interface (default: direct)')
    return parser.parse_args()


def _args_check(args):
    if os.path.exists(args.result):
        print("Result directory '{:s}' already exists. Continue? [y]/n".format(args.result))
        inp = input()
        if inp not in ('y', ''):
            sys.exit()
    if not os.path.exists(args.gams):
        print("ERROR: GAMS not found ('{:s}')".format(args.gams))
        sys.exit()
    if args.max_time <= 0:
        print("ERROR: Invalid max_time ('{:d}')".format(args.max_time))
        sys.exit()
    if args.kill_time < 0:
        print("ERROR: Invalid kill_time ('{:d}')".format(args.kill_time))
        sys.exit()
    if args.threads < 0:
        print("ERROR: Invalid threads ('{:d}')".format(args.threads))
        sys.exit()

    if len(args.gamsopt) == 0:
        gamsopt = [[('id', 0)]]
    else:
        gamsopt = []
        for i, configuration in enumerate(args.gamsopt.split(";")):
            gamsopt.append([('id', i)])
            for option in configuration.split(","):
                gamsopt[-1].append(tuple(option.split("=")))
    args.gamsopt = gamsopt


def _configuration_name(conf):
    name = ''
    for i, (_, option) in enumerate(conf):
        if i > 0:
            name += '_'
        name += str(option)
    return name


def _jobs_create(model_path, runner, args):
    models = sorted(glob.glob(os.path.join(model_path, "*." + runner.modelfile_ext)))
    jobs = queue.Queue()
    timing = time.time()
    k = 1
    for conf in args.gamsopt:
        for model in models:
            if k > args.jobs_max:
                break
            k += 1
            filename = os.path.basename(model)
            filename = os.path.splitext(filename)[0]
            jobs.put((filename, conf, timing))
    return jobs


def _jobs_start(jobs, runner, model_path, args):

    for i in range(args.threads):
        jobs.put(None)

    if args.threads == 1:
        _job_process(0, jobs, runner, model_path, args)
    else:
        threads = []
        for i in range(args.threads):
            thread = threading.Thread(target=_job_process, args=(i, jobs, runner, model_path, args))
            threads.append(thread)
            threads[-1].start()

        for i in range(args.threads):
            threads[i].join()


def _job_process(thread_id, jobs, runner, model_path, args):
    # pylint: disable=too-many-locals,too-many-branches
    while True:
        job = jobs.get()
        if job is None:
            break

        filename = job[0]
        file = filename + "." + runner.modelfile_ext
        conf = job[1]
        conf_name = _configuration_name(conf)
        time_start = job[2]
        workdir = os.path.abspath(os.path.join(args.result, conf_name, filename))

        overall_timing = time.time() - time_start
        if os.path.exists(workdir) or overall_timing > args.jobs_max_time:
            print("[{:4d}|{:2d}|{:8.1f}] {:3s} {:20s} {:30s} {:2d} {:2d} {:8.3f}: {:s}".
                  format(jobs.qsize()-1, thread_id, overall_timing, runner.modelfile_ext,
                         conf_name[:20], filename, 0, 0, 0, '\033[94mskip\033[0m'))
            continue

        # init job
        os.makedirs(workdir)
        copyfile(os.path.join(model_path, file), os.path.join(workdir, file))

        # run
        time_used = time.time()
        trc, stdout, stderr = runner.run(workdir, filename, conf, args.max_time,
                                         args.kill_time)
        time_used = time.time() - time_used
        solvestat = trc.record['SolverStatus']
        modelstat = trc.record['ModelStatus']
        if solvestat is None:
            solvestat = 0
        if modelstat is None:
            modelstat = 0

        # process status
        if stdout:
            status = '\033[91mstdout \033[0m'
        elif stderr:
            status = '\033[91mstderr \033[0m'
        elif solvestat == 6:
            status = '\033[93mcapability \033[0m'
        elif solvestat == 2:
            status = '\033[93mmaxiter \033[0m'
        elif solvestat == 3:
            status = '\033[93mmaxtime \033[0m'
        elif solvestat != 1:
            status = '\033[91mfail \033[0m'
        elif 11 <= modelstat <= 14:
            status = '\033[91mfail \033[0m'
        else:
            status = '\033[92mok \033[0m'
        overall_timing = time.time() - time_start

        print("[{:4d}|{:2d}|{:8.1f}] {:3s} {:20s} {:30s} {:2d} {:2d} {:8.3f}: {:s}".
              format(jobs.qsize()-1, thread_id, overall_timing, runner.modelfile_ext,
                     conf_name[:20], filename, solvestat, modelstat, time_used,
                     status))


def _traces_merge(conf, args):
    conf_name = _configuration_name(conf)
    for trc in glob.glob(os.path.join(args.result, conf_name, "*.trc")):
        os.remove(trc)

    models = sorted(glob.glob(os.path.join(args.result, conf_name, "*")))
    trc = Trace()
    for model in models:
        trc.append_trc(os.path.join(model, "trace.trc"))
    trc.write(os.path.join(args.result, conf_name, 'trace.trc'))


def _run():
    # pylint: disable=import-outside-toplevel
    args = _args()
    _args_check(args)

    # start runner
    if args.interface == 'direct':
        from src.runner_direct import RunnerDirect
        runner = RunnerDirect(args.gams)
    elif args.interface == 'pyomo':
        from src.runner_pyomo import RunnerPyomo
        runner = RunnerPyomo()
    elif args.interface == 'jump':
        from src.runner_jump import RunnerJump
        if args.threads == 1:
            runner = RunnerJump(args.gams, use_pyjulia=True)
        else:
            runner = RunnerJump(args.gams, use_pyjulia=False)

    # select model files
    if args.testset == 'minlplib':
        model_path = os.path.join('testsets', 'minlplib', runner.modelfile_ext)
    elif args.testset == 'princetonlib':
        model_path = os.path.join('testsets', 'princetonlib', runner.modelfile_ext)

    # create jobs
    jobs = _jobs_create(model_path, runner, args)
    _jobs_start(jobs, runner, model_path, args)

    for conf in args.gamsopt:
        _traces_merge(conf, args)


if __name__ == '__main__':
    _run()
