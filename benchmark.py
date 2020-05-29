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

from src.trace import Trace, TraceRecord

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
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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
            trc = TraceRecord()
            status_color = '\033[94m'
            status = 'skip'
            output = '{:4d} '.format(jobs.qsize()-1)
            output += '{:2d} '.format(thread_id)
            output += '{:2d} │ '.format(conf[0][1])
            output += '{:35s} │ '.format(filename + '.' + runner.modelfile_ext)
            if trc.record['SolverStatus'] is None:
                output += '{:2s} '.format('')
            else:
                output += '{:2d} '.format(trc.record['SolverStatus'])
            if trc.record['ModelStatus'] is None:
                output += '{:2s} '.format('')
            else:
                output += '{:2d} '.format(trc.record['ModelStatus'])
            output += '{:s}'.format(status_color)
            output += '{:7s}'.format(status)
            output += '{:s} │ '.format('\033[0m')
            if trc.record['ObjectiveValueEstimate'] is None:
                output += '{:10s} '.format('')
            else:
                output += '{: 9.3e} '.format(trc.record['ObjectiveValueEstimate'])
            if trc.record['ObjectiveValue'] is None:
                output += '{:10s} '.format('')
            else:
                output += '{: 9.3e} '.format(trc.record['ObjectiveValue'])
            output += '{:s}'.format(status_color)
            output += '{:4s}'.format(status)
            output += '{:s} │ '.format('\033[0m')
            output += '{:8s} '.format('')
            if trc.record['ETInterface'] is None:
                output += '{:8s} '.format('')
            else:
                output += '{:8.3f} '.format(trc.record['ETInterface'])
            if trc.record['SolverTime'] is None:
                output += '{:8s} '.format('')
            else:
                output += '{:8.3f} '.format(trc.record['SolverTime'])
            output += '{:s}'.format(status_color)
            output += '{:7s}'.format(status)
            output += '{:s} │ '.format('\033[0m')
            output += '{:8.1f} │'.format(overall_timing)
            print(output)
            continue

        # init job
        os.makedirs(workdir)
        copyfile(os.path.join(model_path, file), os.path.join(workdir, file))

        # run
        time_used = time.time()
        trc, stdout, stderr = runner.run(workdir, filename, conf, args.max_time,
                                         args.kill_time)
        time_used = time.time() - time_used

        # process status
        if stdout:
            status_color = '\033[91m'
            status = 'stdout'
        elif stderr:
            status_color = '\033[91m'
            status = 'stderr'
        elif trc.record['SolverStatus'] == 6:
            status_color = '\033[93m'
            status = 'capabil'
        elif trc.record['SolverStatus'] == 2:
            status_color = '\033[93m'
            status = 'maxiter'
        elif trc.record['SolverStatus'] == 3:
            status_color = '\033[93m'
            status = 'maxtime'
        elif trc.record['SolverStatus'] != 1:
            status_color = '\033[91m'
            status = 'fail'
        elif 11 <= trc.record['ModelStatus'] <= 14:
            status_color = '\033[91m'
            status = 'fail'
        else:
            status_color = '\033[92m'
            status = 'ok'

        # process time
        time_status_color = '\033[92m'
        time_status = 'ok'
        if trc.record['SolverTime'] is not None:
            if trc.record['SolverTime'] > args.max_time and trc.record['SolverStatus'] != 3:
                time_status_color = '\033[91m'
                time_status = 'fail'
            elif trc.record['SolverTime'] > args.max_time:
                time_status_color = '\033[93m'
                time_status = 'maxtime'
            elif trc.record['SolverTime'] > args.max_time + args.kill_time:
                time_status_color = '\033[91m'
                time_status = 'maxtime'
        elif trc.record['ETInterface'] is not None:
            if trc.record['ETInterface'] > args.max_time + args.kill_time:
                time_status_color = '\033[91m'
                time_status = 'maxtime'

        overall_timing = time.time() - time_start

        # output
        output = '{:4d} '.format(jobs.qsize()-1)
        output += '{:2d} '.format(thread_id)
        output += '{:2d} │ '.format(conf[0][1])
        output += '{:35s} │ '.format(filename + '.' + runner.modelfile_ext)
        if trc.record['SolverStatus'] is None:
            output += '{:2s} '.format('')
        else:
            output += '{:2d} '.format(trc.record['SolverStatus'])
        if trc.record['ModelStatus'] is None:
            output += '{:2s} '.format('')
        else:
            output += '{:2d} '.format(trc.record['ModelStatus'])
        output += '{:s}'.format(status_color)
        output += '{:7s}'.format(status)
        output += '{:s} │ '.format('\033[0m')
        if trc.record['ObjectiveValueEstimate'] is None:
            output += '{:10s} '.format('')
        else:
            output += '{: 9.3e} '.format(trc.record['ObjectiveValueEstimate'])
        if trc.record['ObjectiveValue'] is None:
            output += '{:10s} '.format('')
        else:
            output += '{: 9.3e} '.format(trc.record['ObjectiveValue'])
        output += '{:s}'.format('\033[92m')
        output += '{:4s}'.format('ok')
        output += '{:s} │ '.format('\033[0m')
        output += '{:8.3f} '.format(time_used)
        if trc.record['ETInterface'] is None:
            output += '{:8s} '.format('')
        else:
            output += '{:8.3f} '.format(trc.record['ETInterface'])
        if trc.record['SolverTime'] is None:
            output += '{:8s} '.format('')
        else:
            output += '{:8.3f} '.format(trc.record['SolverTime'])
        output += '{:s}'.format(time_status_color)
        output += '{:7s}'.format(time_status)
        output += '{:s} │ '.format('\033[0m')
        output += '{:8.1f} │'.format(overall_timing)
        print(output)


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
