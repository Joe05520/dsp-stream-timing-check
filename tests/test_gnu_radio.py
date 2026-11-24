import json
import os
import subprocess
import sys
import unittest

from stream_timing.fixtures import FIXTURES


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "stream_timing", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "GR_CONF_LOG_LOG_FILE": "stdout"},
    )


class CLITest(unittest.TestCase):
    def test_rejects_invalid_chunk_before_runtime_import(self) -> None:
        result = run_cli("--chunk", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive signed 32-bit integer", result.stderr)
        self.assertEqual(result.stdout, "")


class GNURadioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import gnuradio
        except ModuleNotFoundError as error:
            if error.name != "gnuradio":
                raise
            raise unittest.SkipTest("GNU Radio is unavailable to this interpreter") from error

    def test_cli_observes_the_same_tags_across_scheduler_caps(self) -> None:
        chunks = (1, 3, 8, 32, 128)
        expected = {
            "around_input_boundaries": (
                84, {"before-32": 21, "at-32": 21, "after-32": 22,
                     "before-64": 42, "at-64": 43, "after-64": 43}, {},
            ),
            "colliding_output_offsets": (
                84, {"from-10": 7, "from-11-a": 7, "from-11-b": 7}, {},
            ),
            "finite_boundaries": (
                3, {"first": 0, "middle-a": 1, "middle-b": 1, "last-valid": 2},
                {"end-a": 3, "end-b": 3},
            ),
        }
        args = [arg for chunk in chunks for arg in ("--chunk", str(chunk))]
        result = run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"Invalid JSON on stdout: {error}; prefix={result.stdout[:500]!r}")
        self.assertTrue(report["passed"])
        self.assertEqual(
            [(run["fixture"], run["resampler_max_noutput_items"]) for run in report["runs"]],
            [(fixture.name, chunk) for fixture in FIXTURES for chunk in chunks],
        )
        for run in report["runs"]:
            with self.subTest(fixture=run["fixture"], cap=run["resampler_max_noutput_items"]):
                output_items, present, past_end = expected[run["fixture"]]
                self.assertEqual(run["output_items"], output_items)
                self.assertTrue(run["passed"])
                self.assertTrue(run["gnu_radio_version"])
                rows = {row["event_id"]: row for row in run["events"]}
                self.assertCountEqual(
                    [row["event_id"] for row in run["events"]], present.keys() | past_end.keys()
                )
                for event_id, offset in present.items():
                    self.assertEqual(rows[event_id]["expected_output_offset"], offset)
                    self.assertEqual(rows[event_id]["observed_output_offsets"], [offset])
                    self.assertFalse(rows[event_id]["outside_output"])
                    self.assertEqual(rows[event_id]["problems"], [])
                for event_id, offset in past_end.items():
                    self.assertEqual(rows[event_id]["expected_output_offset"], offset)
                    self.assertEqual(rows[event_id]["observed_output_offsets"], [])
                    self.assertTrue(rows[event_id]["outside_output"])
                    self.assertEqual(rows[event_id]["problems"], [])
