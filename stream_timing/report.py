"""Compare event IDs and offsets without relying on tag arrival order."""

from collections import defaultdict
from dataclasses import dataclass

from .fixtures import Fixture
from .model import Event


@dataclass(frozen=True)
class EventComparison:
    event_id: str
    input_offset: int | None
    expected_output_offset: int | None
    observed_output_offsets: tuple[int, ...]
    outside_output: bool
    problems: tuple[str, ...]


def compare_events(
    fixture: Fixture, observed: tuple[Event, ...], output_items: int
) -> tuple[EventComparison, ...]:
    expected = {
        event.event_id: (event.offset, fixture.contract.output_offset(event.offset))
        for event in fixture.input_events
    }
    by_id: dict[str, list[int]] = defaultdict(list)
    for event in observed:
        by_id[event.event_id].append(event.offset)

    comparisons = []
    for event_id in sorted(expected.keys() | by_id.keys()):
        input_offset, expected_offset = expected.get(event_id, (None, None))
        offsets = tuple(sorted(by_id[event_id]))
        outside = expected_offset is not None and expected_offset >= output_items
        problems = []
        if expected_offset is None:
            problems.append("unexpected")
        if expected_offset is not None and not outside and not offsets:
            problems.append("missing")
        if len(offsets) > 1:
            problems.append("duplicate")
        if expected_offset is not None and any(offset != expected_offset for offset in offsets):
            problems.append("shifted")
        if any(offset >= output_items for offset in offsets):
            problems.append("observed_outside_output")
        comparisons.append(
            EventComparison(event_id, input_offset, expected_offset, offsets, outside, tuple(problems))
        )
    return tuple(comparisons)
