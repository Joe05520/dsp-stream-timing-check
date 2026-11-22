"""Exact arithmetic for the time-grid contract used by synthetic stream fixtures."""

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Event:
    event_id: str
    offset: int

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must not be empty")
        if self.offset < 0:
            raise ValueError("offset must be nonnegative")


@dataclass(frozen=True)
class TimingContract:
    """Map nonnegative input indices onto an output sample grid.

    Phase and delay use ticks at the upsampled rate, not input or output samples.
    The default represents absolute scheduler tag offsets without delay compensation.
    """

    interpolation: int
    decimation: int
    phase_ticks: Fraction = Fraction(0)
    delay_ticks: Fraction = Fraction(0)

    def __post_init__(self) -> None:
        if self.interpolation <= 0 or self.decimation <= 0:
            raise ValueError("interpolation and decimation must be positive")

    def output_position(self, input_offset: int) -> Fraction:
        if input_offset < 0:
            raise ValueError("input offset must be nonnegative")
        ticks = input_offset * self.interpolation + self.delay_ticks - self.phase_ticks
        return Fraction(ticks) / self.decimation

    def output_offset(self, input_offset: int) -> int:
        """Snap a nonnegative position to the nearest item, with half ties forward."""
        position = self.output_position(input_offset)
        if position < 0:
            raise ValueError("event position precedes the output sample grid")
        return int(position + Fraction(1, 2))

    def map_event(self, event: Event) -> Event:
        return Event(event.event_id, self.output_offset(event.offset))
