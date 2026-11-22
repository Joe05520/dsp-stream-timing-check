from fractions import Fraction
import unittest

from stream_timing.fixtures import FIXTURES, Fixture
from stream_timing.model import Event, TimingContract


class TimingContractTest(unittest.TestCase):
    def test_half_ties_round_forward(self) -> None:
        contract = TimingContract(1, 2)
        self.assertEqual([contract.output_offset(i) for i in range(5)], [0, 1, 1, 2, 2])

    def test_large_indices_preserve_half_ties(self) -> None:
        self.assertEqual(TimingContract(1, 2).output_offset(2**54 + 1), 2**53 + 1)

    def test_phase_and_delay_use_upsampled_ticks(self) -> None:
        contract = TimingContract(3, 2, phase_ticks=Fraction(1), delay_ticks=Fraction(1, 2))
        self.assertEqual(contract.output_position(2), Fraction(11, 4))
        self.assertEqual(contract.output_offset(2), 3)

    def test_event_before_output_origin(self) -> None:
        contract = TimingContract(3, 2, phase_ticks=Fraction(1))
        self.assertEqual(contract.output_position(0), Fraction(-1, 2))
        with self.assertRaisesRegex(ValueError, "precedes"):
            contract.output_offset(0)

    def test_invalid_rates_and_input_offset(self) -> None:
        for interpolation, decimation in [(0, 2), (3, -1)]:
            with self.subTest(interpolation=interpolation, decimation=decimation):
                with self.assertRaises(ValueError):
                    TimingContract(interpolation, decimation)
        with self.assertRaises(ValueError):
            TimingContract(2, 3).output_offset(-1)


class FixtureTest(unittest.TestCase):
    def test_boundary_offsets_have_independent_expected_values(self) -> None:
        fixture = FIXTURES[0]
        self.assertEqual(len(fixture.samples()), 128)
        self.assertEqual(fixture.samples()[:4], (-1.0, -0.875, -0.75, -0.625))
        expected = [
            ("before-32", 21),
            ("at-32", 21),
            ("after-32", 22),
            ("before-64", 42),
            ("at-64", 43),
            ("after-64", 43),
        ]
        self.assertEqual(
            [(event.event_id, event.offset) for event in fixture.expected_events()],
            expected,
        )

    def test_distinct_ids_are_preserved_at_the_same_output_offset(self) -> None:
        events = FIXTURES[1].expected_events()
        self.assertEqual([event.offset for event in events], [7, 7, 7])
        self.assertEqual([event.event_id for event in events], ["from-10", "from-11-a", "from-11-b"])

    def test_fixture_rejects_out_of_range_and_duplicate_events(self) -> None:
        contract = TimingContract(2, 3)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            Fixture("out_of_range", contract, 8, (Event("x", 8),))
        with self.assertRaisesRegex(ValueError, "unique"):
            Fixture("duplicate", contract, 8, (Event("x", 1), Event("x", 2)))


if __name__ == "__main__":
    unittest.main()
