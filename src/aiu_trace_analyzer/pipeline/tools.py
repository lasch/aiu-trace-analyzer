# Copyright 2024-2025 IBM Corporation

import hashlib
import json
import copy

from aiu_trace_analyzer.types import TraceEvent
import aiu_trace_analyzer.logger as aiulog


class PipelineContextTool:
    def __init__(self) -> None:
        pass

    def generate_filename(self, fname, purpose="summary", extension="csv") -> str:
        # build a filename from the provided output file
        # remove ".pt.trace" if present as it is only needed for the output json for tensorboard use
        fname = fname.replace(".pt.trace", "")

        # insert _summary before the last '.' and replace the .nnn with .csv
        fcomponents = fname.split('.')
        assert len(fcomponents) >= 1, "Filename cannot be empty."
        if len(fcomponents)==1:
            fcomponents.append(extension)

        fcomponents[-2] += "_" + purpose
        fcomponents[-1] = extension

        return '.'.join(fcomponents)

    def is_FLEX_event(event:TraceEvent) -> bool:
        '''
        Returns True for events that do not contain the information that torch profiler would add
        '''
        is_torch = "args" in event and ("External id" in event["args"] or "Python id" in event["args"])
        return (is_torch == False)


class AutopilotDetail:
    def __init__(self, kernelmap: dict = {}) -> None:
        self.kernelmap = copy.deepcopy(kernelmap)

    def hash(self, input) -> int:
        return hashlib.shake_256(input).digest()

    def table_hash(self):
        tableh = hashlib.sha256()
        for kernel_id in sorted(self.kernelmap.keys()):
            tableh.update(str(kernel_id).encode())

        return tableh.hexdigest()


class KernelDetailsDB:
    """
    The lists/database functionality receives a hash and maps it to:
     * the reference to a measured mapping: kernel_name -> runtime_percentage
    """

    def __init__(self, db_url:str, autopilot: bool) -> None:
        self.db_url = db_url
        self.autopilot = autopilot
        try:
            with open(self.db_url, 'r') as db:
                self.data = json.load(db)
        except:
            aiulog.log(aiulog.WARN, "APD: Unable to find an existing kernel db. Creating new at:", self.db_url)
            self.data = {}

    def __del__(self):
        self.persist_db()

    def persist_db(self):
        if self.autopilot:
            return
        try:
            with open(self.db_url, 'w') as db:
                aiulog.log(aiulog.DEBUG, "APD: Exporting kernel detail db into:", self.db_url)
                json.dump(self.data, db)
        except:
            aiulog.log(aiulog.ERROR, "APD: Failed to export/refresh kernel datail db into:", self.db_url)


    def insert(self, hash:str, mapping_table:AutopilotDetail):
        self.data[hash] = mapping_table

    def retrieve(self, hash:str) -> AutopilotDetail:
        try:
            return self.data[hash]
        except KeyError:
            aiulog.log(aiulog.WARN, "APD: Found no data from previous run with autopilot=0.")
            return {}
