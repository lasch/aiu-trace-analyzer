# Copyright 2024-2025 IBM Corporation

from typing import NamedTuple
from pathlib import Path

# define TraceEvent to be a dictionary for consistency
class TraceEvent(dict):
    pass


class GlobalIngestData(object):
    _jobmap = None

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._jobmap = {}
        return super(GlobalIngestData, cls).__new__(cls)

    @classmethod
    def add_job_info(cls, source_uri: str) -> int:
        jobhash = hash(source_uri) % 10000
        if jobhash not in cls._jobmap:
            cls._jobmap[jobhash] = Path(source_uri).name
        return jobhash

    @classmethod
    def get_job(cls, jobhash: int) -> str:
        try:
            return cls._jobmap[jobhash]
        except KeyError:
            print("jobmap empty")
            return "Not Available"
