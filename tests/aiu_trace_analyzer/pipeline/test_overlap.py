# Copyright 2024-2025 IBM Corporation

import pytest

from aiu_trace_analyzer.pipeline.context import AbstractContext
from aiu_trace_analyzer.pipeline.overlap import recombine_cpu_events
from aiu_trace_analyzer.types import TraceEvent

list_of_cpu_combine_tests = [
    ({"name":"AIU Roundtrip","ph":"X","tid":2000,"args":{"some":"random"}},{"name":"AIU Roundtrip","ph":"X","tid":2000,"args":{"some":"random"}}),  # wrong name -> do not touch
    ({"name":"AIU Roundtrip","ph":"X","tid":2000},{"name":"AIU Roundtrip","ph":"X","tid":2000}),                                               # wrong name (no args) -> do not touch
    ({"name":"cpu_event1","ph":"X","tid":2000,"args":{"some":"random"}},{"name":"cpu_event1","ph":"X","tid":1000,"args":{"some":"random"}}),   # regular CPU -> update
    ({"name":"aiu_event1","ph":"X","tid":3000,"args":{"TS1":123456}},{"name":"aiu_event1","ph":"X","tid":3000,"args":{"TS1":123456}}),         # aiu event -> do not touch
    ({"name":"cpu_event2","ph":"X","tid":3000},{"name":"cpu_event2","ph":"X","tid":1000}),                                                     # cpu without args -> update
    ({"name":"cpu_event3","ph":"b","tid":3000},{"name":"cpu_event3","ph":"b","tid":3000}),                                                     # not X type -> do not touch
]

@pytest.mark.parametrize("input,expected", list_of_cpu_combine_tests)
def test_get_cycles(input:TraceEvent, expected:TraceEvent):
    modified = recombine_cpu_events(input, context=None, config={"cpu_stream_tid":1000})
    assert modified[0] == expected
