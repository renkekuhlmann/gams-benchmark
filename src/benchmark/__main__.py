#!/usr/bin/env python3
"""
GAMS Benchmark

Author: Renke Kuhlmann, GAMS Software GmbH
"""

import argparse
import os
import sys


from scheduler import Scheduler
from output import Output

def _check_int_positive(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not integer" % value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is not positive" % ivalue)
    return ivalue

def _check_int_nonnegative(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not integer" % value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is not positive" % ivalue)
    return ivalue

def _check_str_path(value):
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError("%s is not a valid path" % value)
    return value

def _arguments():
    parser = argparse.ArgumentParser(description='Benchmark GAMS.')
    parser.add_argument('--testset',
                        type=str,
                        default='minlplib',
                        choices=['minlplib', 'princetonlib', 'other'],
                        help='Name of testset (default: minlplib)')
    parser.add_argument('--modelpath',
                        type=str,
                        default='',
                        help='Path to models (.gms, .py or .jl) if testset=other')
    parser.add_argument('--result',
                        type=str,
                        default='latest',
                        help='Result directory (default: latest)')
    parser.add_argument('--gams',
                        type=_check_str_path,
                        default='/opt/gams',
                        help='Path to GAMS (default: /opt/gams)')
    parser.add_argument('--gamsopt',
                        type=str,
                        default='',
                        help='GAMS Options, format: gamsopt1=value1,gamsopt2=value2...')
    parser.add_argument('--max_time',
                        type=_check_int_positive,
                        default='60',
                        help='Max time for solve (default: 60)')
    parser.add_argument('--kill_time',
                        type=_check_int_nonnegative,
                        default='30',
                        help='Time added to max_time before process is killed (default: 30)')
    parser.add_argument('--threads',
                        type=_check_int_nonnegative,
                        default='1',
                        help='Threads used to solve <n> models in parallel (default: 1)')
    parser.add_argument('--max_jobs',
                        type=_check_int_positive,
                        default=sys.maxsize,
                        help='Maximum number of jobs to be added from testset')
    parser.add_argument('--max_total_time',
                        type=_check_int_positive,
                        default=sys.maxsize,
                        help='Maximum time of benchmark until no further jobs are started')
    parser.add_argument('--interface',
                        type=str,
                        default='direct',
                        choices=['direct', 'pyomo', 'jump'],
                        help='Call GAMS through interface (default: direct)')
    parser.add_argument('--output',
                        type=str,
                        default='jobs|name|config|model|status|objective|time',
                        help='Output columns separated by "|" '
                             '(default: jobs|name|config|model|status|objective|time)')
    args = parser.parse_args()

    # check arguments
    if args.testset == 'other':
        args.modelpath = _check_str_path(args.modelpath)
    if os.path.exists(args.result):
        print("Result directory '{:s}' already exists. Continue? [y]/n".format(args.result))
        inp = input()
        if inp not in ('y', ''):
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

    return args


def _main():
    # pylint: disable=import-outside-toplevel
    args = _arguments()

    # start runner
    if args.interface == 'direct':
        from runner_direct import RunnerDirect
        runner = RunnerDirect(args.gams)
    elif args.interface == 'pyomo':
        from runner_pyomo import RunnerPyomo
        runner = RunnerPyomo()
    elif args.interface == 'jump':
        from runner_jump import RunnerJump
        if args.threads == 1:
            # runner = RunnerJump(args.gams, use_pyjulia=True)
            runner = RunnerJump(args.gams, use_pyjulia=False)
        else:
            runner = RunnerJump(args.gams, use_pyjulia=False)

    # select model files
    if args.testset == 'minlplib':
        model_path = os.path.join('testsets', 'minlplib', runner.modelfile_ext)
        solu_file = os.path.join('testsets', 'minlplib', 'minlplib.solu')
    elif args.testset == 'princetonlib':
        model_path = os.path.join('testsets', 'princetonlib', runner.modelfile_ext)
        solu_file = None
    elif args.testset == 'other':
        model_path = args.modelpath
        solu_file = None

    # run benchmark
    scheduler = Scheduler(runner, args.result, args.gamsopt, Output(args.output))
    scheduler.create(model_path, args.max_jobs, args.max_time, args.kill_time, solu_file)
    scheduler.run(args.threads, args.max_total_time)


if __name__ == '__main__':
    _main()
