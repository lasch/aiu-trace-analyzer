# Copyright 2024-2025 IBM Corporation

import json
from pathlib import Path


class StageProfile:
    def __init__(self):
        self.profile = {}

    @classmethod
    def from_json(cls, file: Path):
        with open(file, 'r') as config_fd:
            profile_data = json.load(config_fd)
            profile = StageProfile()
            profile.profile = profile_data

        return profile
