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


    def model_type(self):
        """
        Returns the model type
        """
        return self.trace.record['ModelType']


    def direction(self):
        """
        Returns the optimization sense
        """
        return self.trace.record['Direction']


    def solver(self):
        """
        Returns the solver name
        """
        return self.trace.record['SolverName']


    def n_variables(self):
        """
        Returns the number of variables
        """
        return self.trace.record['NumberOfVariables']


    def n_constraints(self):
        """
        Returns the number of constraints
        """
        return self.trace.record['NumberOfEquations']


    def n_nonzeros(self):
        """
        Returns the number of nonzeros
        """
        return self.trace.record['NumberOfNonZeros']


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
