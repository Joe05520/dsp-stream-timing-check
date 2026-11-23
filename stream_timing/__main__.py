"""Print a machine-readable report for the built-in GNU Radio fixtures."""

import argparse
from dataclasses import asdict
import json
import sys

from .fixtures import FIXTURES
from .gnu_radio import TAG_KEY, TAPS, run_fixture
from .report import compare_events


DEFAULT_CHUNKS = (8, 32, 128)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m stream_timing", description=__doc__)
    fixtures = {fixture.name: fixture for fixture in FIXTURES}
    parser.add_argument(
        "--fixture", choices=fixtures, action="append",
        help="repeat to select multiple fixtures (default: all)",
    )
    parser.add_argument(
        "--chunk", type=int, action="append",
        help="resampler max_noutput_items, repeatable (default: 8, 32, 128)",
    )
    args = parser.parse_args()
    chunks = args.chunk or DEFAULT_CHUNKS
    if any(not 1 <= chunk <= 2**31 - 1 for chunk in chunks):
        parser.error("--chunk must be a positive signed 32-bit integer")

    runs = []
    try:
        for name in args.fixture or fixtures:
            fixture = fixtures[name]
            for chunk in chunks:
                observation = run_fixture(fixture, chunk)
                events = compare_events(fixture, observation.events, observation.output_items)
                passed = observation.output_items > 0 and not any(event.problems for event in events)
                runs.append({
                    "fixture": fixture.name,
                    "gnu_radio_version": observation.runtime_version,
                    "resampler_max_noutput_items": observation.resampler_max_noutput_items,
                    "graph_max_noutput_items": observation.graph_max_noutput_items,
                    "input_items": fixture.input_sample_count,
                    "consumed_input_items": observation.consumed_input_items,
                    "output_items": observation.output_items,
                    "events": [asdict(event) for event in events],
                    "passed": passed,
                })
    except ImportError as error:
        print(f"GNU Radio and PMT must be available to this Python interpreter ({error}).", file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f"GNU Radio run failed for {name} with chunk {chunk} ({error}).", file=sys.stderr)
        return 2

    passed = all(run["passed"] for run in runs)
    report = {
        "resampler": "rational_resampler_ccf",
        "interpolation": 2,
        "decimation": 3,
        "taps": TAPS,
        "tag_key": TAG_KEY,
        "runs": runs,
        "passed": passed,
    }
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
