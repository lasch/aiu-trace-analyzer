# Copyright 2024-2025 IBM Corporation

import pytest
import importlib

from conftest import extend_args_with_tmpout, shared_tmp_path, get_intermediate_filename
from aiu_trace_analyzer.ingest.ingestion import JsonEventTraceIngest
from aiu_trace_analyzer.pipeline import AbstractContext, AbstractHashQueueContext

@pytest.fixture
def load_variables():
    source = importlib.import_module('aiu_trace_analyzer.pipeline.coll_group')
    variable_names = ['_unify_recv', '_unify_rdma',
                      '_FLOW_IO', '_IO_TYPE_DMAO', '_FLOW_STEP',
                      '_FLOW_SYNC', '_KEY_TYPE', '_TYPE_DONE', '_TYPE_MCAST',
                      '_KEY_PEER', '_TYPE_SEND', '_TYPE_BCLIST']
    return {k: v for k, v in vars(source).items() if not k.startswith("__")}


def test_filename(shared_tmp_path, get_intermediate_filename, load_variables):
    # Check if file exists
    assert shared_tmp_path.exists()
    fname = get_intermediate_filename("*flow_prepare*")[0]

    # Load variable value from coll_group.py
    globals().update(load_variables)

    importer=JsonEventTraceIngest(str(fname), test=True)
    context = AbstractHashQueueContext()

    for event in importer:
        group_id = hash(event["name"])

        # Store X events
        if event["ph"] in "X" and "args" in event:
            context.queues[group_id] = event["name"]

        elif event["ph"] in "F":
            # Check if every "F" event has corresponding "X"
            assert group_id in context.queues

            # Check if "args" is included in event F
            assert "args" not in event

            # Check name format
            assert not _unify_recv.search(event["name"])
            assert not _unify_rdma.search(event["name"])

            # Check if has Peers
            assert len(event[_KEY_PEER]) > 0 or event[_KEY_TYPE] == _TYPE_MCAST


            if _FLOW_STEP in event:
                assert event[_FLOW_STEP] == _STEP_DONE
                assert event[_KEY_TYPE] == _TYPE_DONE
            else:
                assert event[_KEY_TYPE] in {_TYPE_SEND, _TYPE_BCLIST, _TYPE_MCAST}


            if _FLOW_IO in event:
                assert event[_FLOW_IO] == _IO_TYPE_DMAO

            assert event[_FLOW_SYNC] in event["name"]


