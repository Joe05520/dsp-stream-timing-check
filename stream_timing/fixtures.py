"""Small, hardware-independent fixtures for fixed-rate tag propagation."""

from dataclasses import dataclass

from .model import Event, TimingContract


@dataclass(frozen=True)
class Fixture:
    name: str
    contract: TimingContract
    input_sample_count: int
    input_events: tuple[Event, ...]

    def __post_init__(self) -> None:
        if self.input_sample_count <= 0:
            raise ValueError("input_sample_count must be positive")
        if any(event.offset >= self.input_sample_count for event in self.input_events):
            raise ValueError("event offset exceeds the input fixture")
        identifiers = {event.event_id for event in self.input_events}
        if len(identifiers) != len(self.input_events):
            raise ValueError("input event IDs must be unique")

    def samples(self) -> tuple[float, ...]:
        return tuple(((offset % 17) - 8) / 8 for offset in range(self.input_sample_count))

    def expected_events(self) -> tuple[Event, ...]:
        return tuple(self.contract.map_event(event) for event in self.input_events)


FIXTURES = (
    Fixture(
        name="around_input_boundaries",
        contract=TimingContract(2, 3),
        input_sample_count=128,
        input_events=(
            Event("before-32", 31),
            Event("at-32", 32),
            Event("after-32", 33),
            Event("before-64", 63),
            Event("at-64", 64),
            Event("after-64", 65),
        ),
    ),
    Fixture(
        name="colliding_output_offsets",
        contract=TimingContract(2, 3),
        input_sample_count=128,
        input_events=(
            Event("from-10", 10),
            Event("from-11-a", 11),
            Event("from-11-b", 11),
        ),
    ),
    Fixture(
        name="finite_boundaries",
        contract=TimingContract(2, 3),
        input_sample_count=6,
        input_events=(
            Event("first", 0),
            Event("middle-a", 1),
            Event("middle-b", 2),
            Event("last-valid", 3),
            Event("end-a", 4),
            Event("end-b", 5),
        ),
    ),
)
