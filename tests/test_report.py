import unittest

from stream_timing.fixtures import FIXTURES, Fixture
from stream_timing.model import Event, TimingContract
from stream_timing.report import compare_events


class ReportTest(unittest.TestCase):
    def test_collision_passes_without_preserving_arrival_order(self) -> None:
        fixture = FIXTURES[1]
        rows = compare_events(fixture, fixture.expected_events()[::-1], 84)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row.observed_output_offsets == (7,) for row in rows))
        self.assertTrue(all(not row.problems for row in rows))

    def test_discrepancies_are_reported_independently_by_id(self) -> None:
        fixture = FIXTURES[1]
        received = (Event("from-11-a", 7), Event("from-11-a", 8), Event("extra", 84))
        rows = {row.event_id: row for row in compare_events(fixture, received, 84)}
        self.assertEqual(rows["from-10"].problems, ("missing",))
        self.assertEqual(rows["from-11-a"].problems, ("duplicate", "shifted"))
        self.assertEqual(rows["from-11-a"].observed_output_offsets, (7, 8))
        self.assertEqual(rows["from-11-b"].problems, ("missing",))
        self.assertEqual(rows["extra"].problems, ("unexpected", "observed_outside_output"))

    def test_output_range_is_half_open(self) -> None:
        fixture = Fixture("tail", TimingContract(2, 3), 128, (Event("tail", 126),))
        row, = compare_events(fixture, (), 84)
        self.assertEqual(row.expected_output_offset, 84)
        self.assertTrue(row.outside_output)
        self.assertEqual(row.problems, ())
        row, = compare_events(fixture, (Event("tail", 84),), 84)
        self.assertEqual(row.problems, ("observed_outside_output",))
        row, = compare_events(fixture, (), 85)
        self.assertFalse(row.outside_output)
        self.assertEqual(row.problems, ("missing",))
