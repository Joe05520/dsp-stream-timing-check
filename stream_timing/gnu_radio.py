"""Run a finite complex stream through GNU Radio's 2/3 rational resampler."""

from dataclasses import dataclass

from .fixtures import Fixture
from .model import Event, TimingContract


TAPS = (1.0, 1.0)
TAG_KEY = "event_id"


@dataclass(frozen=True)
class Observation:
    runtime_version: str
    resampler_max_noutput_items: int
    graph_max_noutput_items: int
    consumed_input_items: int
    output_items: int
    events: tuple[Event, ...]


def run_fixture(fixture: Fixture, chunk: int) -> Observation:
    if fixture.contract != TimingContract(2, 3):
        raise ValueError("the adapter requires rate 2/3 with zero phase and delay")
    if not 1 <= chunk <= 2**31 - 1:
        raise ValueError("chunk must be a positive signed 32-bit integer")

    from gnuradio import blocks, filter, gr
    import pmt

    tags = []
    key = pmt.intern(TAG_KEY)
    source_id = pmt.intern("synthetic_iq")
    for event in fixture.input_events:
        tag = gr.tag_t()
        tag.offset = event.offset
        tag.key = key
        tag.value = pmt.intern(event.event_id)
        tag.srcid = source_id
        tags.append(tag)

    samples = tuple(
        complex(in_phase, ((5 * index % 19) - 9) / 8)
        for index, in_phase in enumerate(fixture.samples())
    )
    graph = gr.top_block()
    source = blocks.vector_source_c(samples, False, 1, tags)
    resampler = filter.rational_resampler_ccf(2, 3, TAPS)
    resampler.set_max_noutput_items(chunk)
    sink = blocks.vector_sink_c()
    graph.connect(source, resampler, sink)

    # A tagged vector source requires room for a whole vector in one work call.
    # Apply the requested cap only to the resampler.
    graph_limit = max(fixture.input_sample_count, chunk)
    graph.run(graph_limit)

    events = tuple(
        Event(pmt.symbol_to_string(tag.value), tag.offset)
        for tag in sink.tags()
        if pmt.eq(tag.key, key)
    )
    return Observation(
        runtime_version=gr.version(),
        resampler_max_noutput_items=chunk,
        graph_max_noutput_items=graph_limit,
        consumed_input_items=resampler.nitems_read(0),
        output_items=len(sink.data()),
        events=events,
    )
