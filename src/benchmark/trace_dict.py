#!/usr/bin/env python3
""" TraceDict """

import os

from trace_record import TraceRecord

class TraceDict:
    """
    Database of Trace Records
    """

    def __init__(self):
        self.records = dict()


    def append(self, trace_record):
        """
        Add trace record to database

        Arguments
        ---------
        trace_record: TraceRecord
            Trace Record to be added
        """
        self.records[trace_record.record['InputFileName']] = trace_record


    def append_trc(self, trcfile):
        """
        Add trace entries located in a trace file to database

        Arguments
        ---------
        trcfile: str
            Path to trace file
        """
        trc = TraceRecord(None)
        trc.load_trc(trcfile)
        self.append(trc)


    def load_solu(self, solufile):
        """
        Loads a solution file to trace format

        Arguments
        ---------
        solufile: str
            Solution file
        """
        if not os.path.exists(solufile):
            return

        with open(solufile, 'r') as fio:
            lines = fio.readlines()

        for line in lines:
            entry = list(filter(None, line.replace('\n', '').split(" ")))
            if len(entry) < 2:
                continue
            if entry[0] == '=opt=':
                trc = TraceRecord(entry[1])
                trc.record['ModelStatus'] = 1
                trc.record['ObjectiveValue'] = float(entry[2])
                trc.record['ObjectiveValueEstimate'] = float(entry[2])
                self.append(trc)
            elif entry[0] == '=inf=':
                trc = TraceRecord(entry[1])
                trc.record['ModelStatus'] = 4
                self.append(trc)
            elif entry[0] == '=best=':
                if entry[1] in self.records:
                    self.records[entry[1]].record['ObjectiveValue'] = float(entry[2])
                else:
                    trc = TraceRecord(entry[1])
                    trc.record['ModelStatus'] = 2
                    trc.record['ObjectiveValue'] = float(entry[2])
                    self.append(trc)
            elif entry[0] == '=bestdual=':
                if entry[1] in self.records:
                    self.records[entry[1]].record['ObjectiveValueEstimate'] = float(entry[2])
                else:
                    trc = TraceRecord(entry[1])
                    trc.record['ModelStatus'] = 2
                    trc.record['ObjectiveValueEstimate'] = float(entry[2])
                    self.append(trc)


    def write(self, trcfile):
        """
        Writes a trace file from database

        Arguments
        ---------
        trcfile: str
            Path to trace file
        """
        if len(self.records) == 0:
            return
        for i, key in enumerate(sorted(self.records.keys())):
            if i == 0:
                self.records[key].write_header(trcfile)
            self.records[key].write_record(trcfile)
