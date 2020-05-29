#!/usr/bin/env python3
""" Result """

class Result:
    """
    Holds the result of a benchmark job
    """

    def __init__(self, trace, stdout, stderr):
        self.trace = trace
        self.stdout = stdout
        self.stderr = stderr


    def name(self):
        """
        Returns the job name
        """
        return self.trace.record['InputFileName']


    def solver_status(self):
        """
        Returns the solver status
        """
        return self.trace.record['SolverStatus']


    def model_status(self):
        """
        Returns the model status
        """
        return self.trace.record['ModelStatus']


    def objective(self):
        """
        Returns the objective function value
        """
        return self.trace.record['ObjectiveValue']


    def objective_estimate(self):
        """
        Returns the objective function estimate
        """
        return self.trace.record['ObjectiveValueEstimate']


    def solver_time(self):
        """
        Returns the solver time
        """
        return self.trace.record['SolverTime']


    def et_interface(self):
        """
        Returns the interface time
        """
        return self.trace.record['ETInterface']
