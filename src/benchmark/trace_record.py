#!/usr/bin/env python3
""" TraceRecord """

import os
import re
import math

TRACE_ENTRIES = [
    'InputFileName', 'ModelType', 'SolverName', 'NLP', 'MIP', 'JulianDate',
    'Direction', 'NumberOfEquations', 'NumberOfVariables',
    'NumberOfDiscreteVariables', 'NumberOfNonZeros', 'NumberOfNonlinearNonZeros',
    'OptionFile', 'ModelStatus', 'SolverStatus', 'ObjectiveValue',
    'ObjectiveValueEstimate', 'ETSolver', 'ETSolve', 'ETInterface', 'ETInterfaceOverhead',
    'SolverTime', 'NumberOfIterations', 'NumberOfDomainViolations', 'NumberOfNodes'
]

TRACE_ENTRIES_STRING = [
    'InputFileName', 'ModelType', 'SolverName', 'NLP', 'MIP', 'OptionFile'
]

TRACE_ENTRIES_INTEGER = [
    'Direction', 'NumberOfEquations', 'NumberOfVariables',
    'NumberOfDiscreteVariables', 'NumberOfNonZeros', 'NumberOfNonlinearNonZeros',
    'ModelStatus', 'SolverStatus', 'NumberOfIterations', 'NumberOfDomainViolations',
    'NumberOfNodes'
]

TRACE_ENTRIES_REAL = [
    'JulianDate', 'ObjectiveValue', 'ObjectiveValueEstimate', 'ETSolver', 'ETSolve',
    'ETInterface', 'ETInterfaceOverhead', 'SolverTime'
]

class TraceRecord:
    """
    Trace Record stores solve attributes that are present in a GAMS trace file
    """

    def __init__(self, filename):
        self.record = dict()
        for key in TRACE_ENTRIES:
            self.record[key] = None
        self.record['InputFileName'] = filename

        # some default values necessary for correct paver input
        self.record['Direction'] = 0
        self.record['SolverStatus'] = 13
        self.record['ModelStatus'] = 12
        self.record['SolverTime'] = 0


    def load_lst(self, lstfile):
        """
        Loads solve attributes from a listing file

        Arguments
        ---------
        lstfile: str
            Path to listing file
        """

        if not os.path.exists(lstfile):
            return

        with open(lstfile, 'r') as fio:
            lines = fio.readlines()

        for line in lines:
            if re.findall(r"^\*\*\*\* SOLVER STATUS.*[0-9]+", line):
                match = re.findall("[0-9]+", line)[0]
                try:
                    self.record['SolverStatus'] = int(match)
                except ValueError:
                    self.record['SolverStatus'] = None

            if re.findall(r"^\*\*\*\* MODEL STATUS.*[0-9]+", line):
                match = re.findall("[0-9]+", line)[0]
                try:
                    self.record['ModelStatus'] = int(match)
                except ValueError:
                    self.record['ModelStatus'] = None

            if re.findall(r"TYPE.*DIRECTION", line):
                tmp = list(filter(None, line.replace('\n', '').split(" ")))
                self.record['ModelType'] = tmp[1]
                if tmp[3] == "MINIMIZE":
                    self.record['Direction'] = 0
                elif tmp[3] == "MAXIMIZE":
                    self.record['Direction'] = 1

            if re.findall(r"RESOURCE USAGE, LIMIT", line):
                match = list(filter(None, line.replace('\n', '').split(" ")))
                try:
                    self.record['SolverTime'] = float(match[3])
                except ValueError:
                    self.record['SolverTime'] = None


    def load_trc(self, trcfile):
        """
        Loads solve attributes from a trace file

        Arguments
        ---------
        trcfile: str
            Path to trace file
        """
        # pylint: disable=too-many-branches,too-many-statements

        with open(trcfile, 'r') as fio:
            lines = fio.readlines()

        header = list()
        header_read = False
        header_it = iter(header)
        traceopt = 3
        for line in lines:
            # read header
            if line[0] == '*':
                # skip GamsSolve, GamsExit line
                if line.find('GamsSolve') >= 0:
                    continue
                if line.find('GamsExit') >= 0:
                    continue

                if line.find('Trace Record Definition') >= 0:
                    header_read = True
                    continue

                if header_read:
                    # remove '*' and spaces
                    line = line[1:].strip()
                    # empty comment line -> end of header
                    if len(line) == 0:
                        header_read = False
                        header_it = iter(header)
                        continue
                    if line[0] == ',':
                        line = line[1:]
                    if line[-1] == ',':
                        line = line[:-1]
                    if line[-2:] == '\\n':
                        traceopt = 5
                        line = line[:-2]

                    # append to trace record definition
                    for key in line.split(','):
                        header.append(key.strip())
                continue

            # get elements
            if traceopt == 3:
                elements = line.split(',')
            elif traceopt == 5:
                elements = [line.replace('\n', '')]
            for element in elements:
                element = element.strip()

                # update iterator
                current_header = next(header_it)
                if current_header == header[-1]:
                    header_it = iter(header)

                # parse element
                if element == "NA" or len(element) == 0:
                    element = None
                if current_header in TRACE_ENTRIES_INTEGER:
                    try:
                        element = int(element)
                    except (ValueError, TypeError):
                        element = None
                if current_header in TRACE_ENTRIES_REAL:
                    try:
                        element = float(element)
                    except (ValueError, TypeError):
                        element = None

                # store element
                if current_header in TRACE_ENTRIES:
                    self.record[current_header] = element


    def write_header(self, trcfile):
        """
        Writes trace file definition to trace file

        Arguments
        ---------
        trcfile: str
            Path to trace file
        """
        with open(trcfile, 'w') as fio:
            fio.write("* Trace Record Definition\n")
            for i, key in enumerate(self.record):
                fio.write("* %s" % key)
                if i < len(self.record)-1:
                    fio.write(",")
                fio.write("\n")
            fio.write("*\n")


    def write_record(self, trcfile):
        """
        Writes the trace record to trace file

        Arguments
        ---------
        trcfile: str
            Path to trace file
        """
        with open(trcfile, 'a') as fio:
            for i, (_, value) in enumerate(self.record.items()):
                if i > 0:
                    fio.write(",")
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    fio.write("NA")
                else:
                    fio.write(str(value))
            fio.write("\n")

    def write(self, trcfile):
        """
        Writes trace file record to trace file incl. trace file definition

        Arguments
        ---------
        trcfile: str
            Path to trace file
        """
        self.write_header(trcfile)
        self.write_record(trcfile)
