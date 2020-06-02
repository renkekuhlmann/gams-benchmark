#!/usr/bin/env python3
""" Output """

class BColors:
    """
    Escape Sequences for colorful command line output
    """
    # pylint: disable=too-few-public-methods
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Output:
    """
    Formats and prints benchmark results
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self):
        self.print_benchmark_meta = True
        self.print_name = True
        self.print_configuration_meta = True
        self.print_job_meta = True
        self.print_status = True
        self.print_objective = True
        self.print_time = True
        self.print_cumtime = True


    def print(self, job, result, cumtime, n_jobs_left, thread_id):
        """
        Formats and prints job result
        """
        # pylint: disable=too-many-arguments
        output = ''
        if self.print_benchmark_meta:
            output += self._output_benchmark_meta(n_jobs_left, thread_id, cumtime) + ' │ '
        if self.print_name:
            output += self._output_name(job) + ' │ '
        if self.print_configuration_meta:
            output += self._output_configuration_meta(job, result) + ' │ '
        if self.print_job_meta:
            output += self._output_job_meta(result) + ' │ '
        if self.print_status:
            output += self._output_status(result) + ' │ '
        if self.print_objective:
            output += self._output_objective(result) + ' │ '
        if self.print_time:
            output += self._output_time(job, result) + ' │ '
        print(output)


    @staticmethod
    def _output_benchmark_meta(n_jobs_left, thread_id, cumtime):
        msg = '{:2d} '.format(thread_id)
        msg += '{:4d} '.format(n_jobs_left)
        msg += '{:8.1f}'.format(cumtime)
        return msg


    @staticmethod
    def _output_name(job):
        return '{:35s}'.format(job.filename())


    @staticmethod
    def _output_configuration_meta(job, result):
        msg = '{:1d} '.format(job.configuration[0][1])
        if result.solver() is None:
            msg += '{:6s}'.format('')
        else:
            msg += '{:6s}'.format(result.solver()[:6])
        return msg


    @staticmethod
    def _output_job_meta(result):
        msg = ''
        if result.model_type() is None:
            msg += '{:5s} '.format('')
        else:
            msg += '{:5s} '.format(result.model_type())
        if result.direction() is None:
            msg += '{:3s} '.format('')
        elif result.direction() == 0:
            msg += 'MIN '
        elif result.direction() == 1:
            msg += 'MAX '
        else:
            msg += '{:3s} '.format('')
        if result.n_variables() is None:
            msg += '{:8s} '.format('')
        else:
            msg += '{:8d} '.format(result.n_variables())
        if result.n_constraints() is None:
            msg += '{:8s} '.format('')
        else:
            msg += '{:8d} '.format(result.n_constraints())
        if result.n_nonzeros() is None:
            msg += '{:8s} '.format('')
        else:
            msg += '{:8d} '.format(result.n_nonzeros())
        return msg


    @staticmethod
    def _output_status(result):
        if result.stdout:
            color = BColors.FAIL
            status = 'stdout'
        elif result.stderr:
            color = BColors.FAIL
            status = 'stderr'
        elif result.solver_status() == 6:
            color = BColors.WARNING
            status = 'capabil'
        elif result.solver_status() == 2:
            color = BColors.WARNING
            status = 'maxiter'
        elif result.solver_status() == 3:
            color = BColors.WARNING
            status = 'maxtime'
        elif result.solver_status() != 1:
            color = BColors.FAIL
            status = 'fail'
        elif 11 <= result.model_status() <= 14:
            color = BColors.FAIL
            status = 'fail'
        else:
            color = BColors.OKGREEN
            status = 'ok'

        msg = ''
        if result.solver_status() is None:
            msg += '{:2s} '.format('')
        else:
            msg += '{:2d} '.format(result.solver_status())
        if result.model_status() is None:
            msg += '{:2s} '.format('')
        else:
            msg += '{:2d} '.format(result.model_status())
        msg += '{:s}'.format(color)
        msg += '{:7s}'.format(status)
        msg += '{:s}'.format(BColors.ENDC)
        return msg


    @staticmethod
    def _output_objective(result):
        msg = ''
        if result.objective_estimate() is None:
            msg += '{:10s} '.format('')
        else:
            msg += '{: 9.3e} '.format(result.objective_estimate())
        if result.objective() is None:
            msg += '{:10s} '.format('')
        else:
            msg += '{: 9.3e} '.format(result.objective())
        msg += '{:s}'.format(BColors.OKGREEN)
        msg += '{:4s}'.format('ok')
        msg += '{:s}'.format(BColors.ENDC)
        return msg


    @staticmethod
    def _output_time(job, result):
        color = BColors.OKGREEN
        status = 'ok'
        if result.solver_time() is not None:
            if result.solver_time() > job.max_time and result.solver_status() != 3:
                color = BColors.FAIL
                status = 'fail'
            elif result.solver_time() > job.max_time:
                color = BColors.WARNING
                status = 'maxtime'
            elif result.solver_time() > job.max_time + job.kill_time:
                color = BColors.FAIL
                status = 'maxtime'
        elif result.et_interface() is not None:
            if result.et_interface() > job.max_time + job.kill_time:
                color = BColors.FAIL
                status = 'maxtime'

        msg = ''
        if result.et_interface() is None:
            msg += '{:8s} '.format('')
        else:
            msg += '{:8.3f} '.format(result.et_interface())
        if result.solver_time() is None:
            msg += '{:8s} '.format('')
        else:
            msg += '{:8.3f} '.format(result.solver_time())
        msg += '{:s}'.format(color)
        msg += '{:7s}'.format(status)
        msg += '{:s}'.format(BColors.ENDC)
        return msg
