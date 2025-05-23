# Copyright 2024-2025 IBM Corporation

import re

import aiu_trace_analyzer.logger as aiulog
from aiu_trace_analyzer.pipeline.context import AbstractContext
from aiu_trace_analyzer.pipeline.hashqueue import AbstractHashQueueContext
from aiu_trace_analyzer.pipeline.tools import PipelineContextTool
from aiu_trace_analyzer.types import TraceEvent
import aiu_trace_analyzer.export.exporter as output

DmaI="DmaI"
DmaO="DmaO"
RDMA="Rdma"

Coll_data_size="Coll_data_size"
AllReduce="AllReduce_all_reduce"

class RefinementContext(AbstractHashQueueContext):
    name_converter = re.compile(r"[_-]\d+")

    def __init__(self, exporter: output.AbstractTraceExporter) -> None:
        super().__init__()
        self.exporter = exporter
        self.meta_exported = False
        self.has_coll_bw = False

    def drain(self) -> list[TraceEvent]:
        # make metadata event export idempotent
        if self.meta_exported:
            return []

        revents = []
        for p,(s,i,l,t) in self.queues.items():
            revents.append({
                "ph": "M", "name": "process_name",
                "pid": p,
                "ts": t,
                "args": { "name": s }
            })
            revents.append({
                "ph": "M", "name": "process_label",
                "pid": p,
                "ts": t,
                "args": { "name": l }
            })
            revents.append({
                "ph": "M", "name": "process_sort_index",
                "pid": p,
                "ts": t,
                "args": { "sort_index": i+10 }
            })

        if self.has_coll_bw:
            revents.append({
                "ph": "M", "name": "process_name",
                "pid": -1,
                "ts": 0,
                "args": { "name": "CollectiveBW" }
            })
            revents.append({
                "ph": "M", "name": "process_sort_index",
                "pid": -1,
                "ts": 0,
                "args": { "sort_index": 0 }
            })

        self.meta_exported = True
        return revents


    def update_event_data_heavy(self, event) -> TraceEvent:
        pid = event["pid"]

        # to group function calls by name without index...
        # ...extract a function index (if any) from the event name
        match = self.name_converter.search(event["name"])
        if match and "args" in event:
            event["args"]["fn_idx"] = event["name"][match.start()+1:match.end()]
        # ...and replace it with _N
            event["name"] = re.sub(self.name_converter, "_N", event["name"], count=1)

        if "coll" in str(event["tid"]):
            event["tid"] = 10000+int(str(event["tid"])[4])

        # ensure events with different PIDs have different TIDs
        event["tid"] = pid*100000 + event["tid"]
        return event

    def update_event_data_light(self, event) -> TraceEvent:

        def _cat_for_regular_event(event: TraceEvent) -> str:
            # Use DmaI and DmaO with Sen to check memcpy event
            if DmaI in event["name"] or DmaO in event["name"]:

                # if no RDMA, a memory copy event
                # else RDMA send and recv event
                if RDMA not in event["name"]:
                    return "gpu_memcpy"
                else:
                    return "user_annotation"

            else:
                if AllReduce in event["name"] and 'Cmpt Exec' in event["name"]:
                    return "user_annotation"
                else:
                    return "kernel"

        def _update_collective_event(event: TraceEvent) -> TraceEvent:
            # if collective call block, change 'cat'
            # and 'name' for communication tb calculation
            if "args" in event and Coll_data_size in event["args"] and AllReduce in event["name"]:
                event["cat"] = "user_annotation"
                event["name"] = "gloo:all_reduce"
                event["external id"] = event["args"].pop("fn_idx")
            else:
                event["cat"] = "cpu_op"
            return event



        pid = event["pid"]

        if isinstance(pid, str):
            aiulog.log(aiulog.WARN, f'TBR: input pid is string: {pid}')
            try:
                pid = int(pid)
            except (ValueError, TypeError):
                pid = hash(pid) % 10000 + 10000

        if "args" in event and "TS1" in event["args"]:
            event["cat"] = _cat_for_regular_event(event)

            event["args"]["device"] = pid
            if pid not in self.queues:
                self.queues[pid] = ("AIU Device"+str(pid), pid*2+1, "AIU", event["ts"])
                self.exporter.add_device(pid, {"type": "AIU", "core": "PT Array", "name":"AIU DD1", "RCU":32, "ScratchMem": 128})
        else:
            event = _update_collective_event(event)

            if isinstance(pid, str):
                event["pid"] = pid + "1000"
            else:
                event["pid"] = pid + 1000

            if event["pid"] not in self.queues:
                self.queues[event["pid"]] = ("Host"+str(pid), pid*2, "cpu", event["ts"])

            # events that are not from flex should appear at the top and thus we shrink the TID
            if not PipelineContextTool.is_FLEX_event(event):
                event["tid"] = int(event["tid"]/10) + (event["tid"] % 10)

        return event


# more significant changes to events that are needed for TB to work
# this function can be disabled with cmd-line flag
def tb_refinement_intrusive(event: TraceEvent, context: AbstractContext) -> list[TraceEvent]:
    assert( isinstance(context, RefinementContext) )

    if event["ph"] in "X":
        event = context.update_event_data_heavy(event)

    return [event]

# more lightweight changes to event that are useful for not just TB (e.g. stats)
# this function CANNOT be disable with cmd-line flag
def tb_refinement_lightweight(event: TraceEvent, context: AbstractContext) -> list[TraceEvent]:
    assert( isinstance(context, RefinementContext) )

    if event["ph"] in "X":
        event = context.update_event_data_light(event)

    # signal to the context that there's a collective bw counter to create meta events with name and sort index
    if event["ph"] == "C" and not context.has_coll_bw:
        context.has_coll_bw |= (event["name"] == "BW allreduce")

    return [event]
