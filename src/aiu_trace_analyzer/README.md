# aiu_trace_analyzer developer info

Base concept for event processing
  * import/ingest
  * process
  * export

## import

Imports are in `ingest` and need to be derived from `AbstractTraceIngest`. All importers need to be iterators providing a single instance of `TraceEvent` (which is a dictionary version of on event from the JSON Trace Format).

## export

Exporter classes are in `export` and need to be derived from `AbstractTraceExporter`.  Exporters need to implement an `export` and a `flush` function:
```
    def export(self, data: list[TraceView.AbstractEventType]):
        ...
    def flush(self):
        ...
```
It's up to the implementor whether `export` immediately exports the input event or whether to buffer the output until `flush` is called.

In addition, there's a way to add device information to the exported file by calling:
```
    exporter.add_device(pid, <device_info_dictionary>)
```

## process

The core of the processing iterates over the import iterators and feeds the events through optionally registered pre-processing hooks one-by-one.  Then converts the `TraceEvent` dictionaries into derived `AbstractEventType` from the `TraceView` class.  After conversion, the events are passed to optionally registered post-processing hooks before they're send to export. When all events are processed, the main engine calls the `flush` function of the exporter to complete the processing.

### pre-processing functions

Pre-processing functions can be registered using:
```
    EventProcessor.registerPreProcess( callback, context: AbstractContext, opt_config: dict)
```

The callback function has to look like this:
```
    <callback_name>( event: TraceEvent, context: AbstractContext) -> list[TraceEvent]
```
Where the input is a single `TraceEvent` and the output is a `list of TraceEvent`s to accommodate situations where a single event requires the creation of multiple events.
The context is an optional parameter (a class derived from `AbstractContext`) to handle any global state that might be necessary for event processing.  Examples for global state can be mapping tables, event queues for reordering, etc.
The `opt_config` argument is an optional way to pass static configuration information to the callback without requiring a context. The function will be provided with a dictionary type input that's set at the time of registration.

The main idea is that each step in the registered sequence of callbacks will see every event that's ingested (and all events that might be created from those along the way) exactly only once.  Any stage is free to hold back events until certain conditions are met (e.g. finding event pairs) but eventually need to make sure to return those events for the main engine to feed those events into the next stages (unless for things like event filtering or merging where the number of events is reduced). It can be thought of the function living inside a for loop that iterates over all events.

There's a [template file](pipeline/template.py) for developing new pipeline steps which also explains how to integrate with the rest of the tool.


### intermedate states

If something goes wrong or for verification purposes, the option `-I` can be used to create a file that contains the events as they are emitted by each of the processing stages. In this case the output file name is postfixed with `_<name_of_processing_function>_<stage_idx>`. Note that some stages might add additional fields to the events that either cannot be viewed in a GUI or the GUIs might not even be able to open those intermediate files.
