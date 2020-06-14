#!/usr/bin/env python3
"""
GAMS Benchmark

Author: Renke Kuhlmann, GAMS Software GmbH
"""

import argparse
import os
import sys


from src.scheduler import Scheduler
from src.output import Output

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
                        type=str,
                        default='/opt/gams',
                        help='Path to GAMS (default: /opt/gams)')
    parser.add_argument('--gamsopt',
                        type=str,
                        default='',
                        help='GAMS Options, format: gamsopt1=value1,gamsopt2=value2...')
    parser.add_argument('--max_time',
                        type=int,
                        default='60',
                        help='Max time for solve (default: 60)')
    parser.add_argument('--kill_time',
                        type=int,
                        default='30',
                        help='Time added to max_time before process is killed (default: 30)')
    parser.add_argument('--threads',
                        type=int,
                        default='1',
                        help='Threads used to solve <n> models in parallel (default: 1)')
    parser.add_argument('--jobs_max',
                        type=int,
                        default=10000000,
                        help='Max jobs')
    parser.add_argument('--jobs_max_time',
                        type=int,
                        default=10000000,
                        help='Max jobs')
    parser.add_argument('--interface',
                        type=str,
                        default='direct',
                        choices=['direct', 'pyomo', 'jump'],
                        help='Call GAMS through interface (default: direct)')
    parser.add_argument('--output',
                        type=str,
                        default='jobs|name|config|model|status|objective|time',
                        help='Output columns separated by "|"'
                             '(default: jobs|name|config|model|status|objective|time)')
    args = parser.parse_args()

    # check arguments
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

    return args


def _main():
    # pylint: disable=import-outside-toplevel
    args = _arguments()

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
    scheduler.create(model_path, args.jobs_max, args.max_time, args.kill_time, solu_file)
    scheduler.run(args.threads, args.jobs_max_time)


if __name__ == '__main__':
    _main()
