# DSP Stream Timing Check development

All dates use Asia/Taipei.

| Day | Work | Acceptance |
| --- | --- | --- |
| 2026-11-22 | Exact timing reference and synthetic fixtures | Standard-library tests for rounding, phase, delay, boundary indices and collisions |
| 2026-11-23 | GNU Radio adapter and CLI | Run a finite headless vector-source/resampler/vector-sink flowgraph with stable event IDs and recorded scheduler settings. Compare missing, unexpected, duplicate and shifted events. |
| 2026-11-24 | Release validation | Run the full test suite and a CLI smoke test with an actual GNU Radio runtime, document the measured result and runtime version, then publish the independent GitHub repo and release if all checks pass. |

Day 2 can use the two fixtures in stream_timing/fixtures.py with GNU Radio 3.10's filter.rational_resampler_fff and explicitly known taps. Convert the synthetic event IDs to PMT values and compare output tags by ID and offset. Recreate the flowgraph for each scheduler setting so state and counters start from zero. Try multiple max_noutput_items settings that the runtime accepts. If testing reporting by injecting a missing or shifted tag, keep that result distinct from the observed GNU Radio result.

The day 1 reference passed under Python 3.12.5. For day 2, an independently built local GNU Radio g3d33e04 successfully imported under Python 3.11.7 with its build environment and exposed the required vector source and rational resampler. A flowgraph execution remains part of day 2.

For the current development Mac, .local/gnu-radio.md records the verified
interpreter and environment. A standard GNU Radio installation can use its
matching Python directly.
