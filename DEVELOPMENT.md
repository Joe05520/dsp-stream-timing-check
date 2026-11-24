# DSP Stream Timing Check development

All dates and times use Asia/Taipei.

| Day | Work | Acceptance |
| --- | --- | --- |
| 2026-11-22 | Exact timing reference and synthetic fixtures | Standard-library tests for rounding, phase, delay, boundary indices and collisions |
| 2026-11-23 | GNU Radio adapter and CLI | Run finite complex I/Q through a headless 2/3 resampler and compare event offsets over several scheduler settings |
| 2026-11-24 | Release validation | Complete boundary and collision QA, minimal fixture, license, CI example and a clean checkout test with actual GNU Radio before release |

## 2026-11-22 reference baseline

Commit `daacba8` records the reference and two synthetic fixtures. The eight
reference tests passed under Python 3.12.5 and were rerun at the start of day 2.

## 2026-11-23 GNU Radio adapter

Started at 17:04 and finished implementation and validation at 17:09. The
Apple Silicon GNU Radio build reported `g3d33e04` with Python 3.11.7. Its public
base commit is [3d33e04a](https://github.com/gnuradio/gnuradio/commit/3d33e04a249b31ef32106d275b927a7c4cf86425).
On the development Mac, the ignored `.local/gnu-radio.md` records the interpreter
and build environment. The public installation examples in the README use the
installed distribution bindings and their matching Python.

- `python -m unittest discover -s tests -v` passed 11/11 under Python 3.12.5 and
  the GNU Radio interpreter. Comparator tests supply synthetic missing,
  duplicate, shifted, unexpected, and out-of-range tags directly.
- `python -m stream_timing` completed 20 sweeps (120 GNU Radio flowgraphs).
  All 20 JSON reports were byte-identical. Each graph sent 128 items, the
  resampler consumed 126, and the sink received 84. The graph-wide cap was 128
  for all runs. The table shows the reference and observed offsets for each
  listed input, in the same order. Each expected ID arrived once.
- A selected-fixture run with repeated `--chunk` arguments passed. Invalid chunk
  `0` and a Python interpreter without GNU Radio both returned status 2.

| Fixture | Resampler caps | Input indices | Expected = observed output indices |
| --- | --- | --- | --- |
| `around_input_boundaries` | 8, 32, 128 | 31, 32, 33, 63, 64, 65 | 21, 21, 22, 42, 43, 43 |
| `colliding_output_offsets` | 8, 32, 128 | 10, 11, 11 | 7, 7, 7 |

These fixtures verify absolute tag coordinates and ID preservation. The reported
cap is a limit on the scheduler request to the resampler. Individual work-call
sizes and physical FIR waveform alignment were outside this measurement. The
finite input has no appended flush samples. The valid sink indices in these
runs were 0 through 83. Other runtime versions and installation methods in the
README remain to be tested.

### GNU Radio source comparison

- GNU Radio 3.10.8.0 and 3.10.12.0 have the same default stream-tag executor
  code. It queries the consumed input interval and rounds the absolute tag
  offset after multiplying by the relative rate. The public `3d33e04a` build
  base has a different internal tag query signature and a separate policy for
  tagged-stream blocks. Its default scaling and rounding still match this
  project's zero-phase, zero-delay contract at these fixture offsets.
  [3.10.8.0 executor](https://github.com/gnuradio/gnuradio/blob/v3.10.8.0/gnuradio-runtime/lib/block_executor.cc#L124-L169),
  [3.10.12.0 executor](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gnuradio-runtime/lib/block_executor.cc#L124-L169),
  [3d33e04a executor](https://github.com/gnuradio/gnuradio/blob/3d33e04a249b31ef32106d275b927a7c4cf86425/gnuradio-runtime/lib/block_executor.cc#L127-L171).
- The rational resampler's rate registration, forecast and work logic agree
  across those three sources. The tagged vector source sets its output
  multiple to the whole fixture length. A preliminary graph-wide cap of 8
  with 127 tagged input items stalled on the tested runtime. The adapter uses
  a per-resampler cap and a graph cap that can accommodate the tagged source.
  [3.10.12.0 resampler](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-filter/lib/rational_resampler_impl.cc),
  [3.10.12.0 vector source](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-blocks/lib/vector_source_impl.cc#L29-L50).
- Issue #7328 describes intermittent loss on 3.10.8.0. The related open PR
  #8270 proposes explicit resampler tag placement using a ceiling-based
  position, which can differ from nearest-index rounding. The original issue
  flowgraph and the proposed patch were outside the day 2 runtime tests.
  [Issue #7328](https://github.com/gnuradio/gnuradio/issues/7328),
  [PR #8270](https://github.com/gnuradio/gnuradio/pull/8270).

## 2026-11-24 release validation

Started at 16:59. Implementation and the local pre-commit regression finished
at 17:01. Added the six-item finite fixture, CLI regression, and Ubuntu 24.04
GitHub Actions workflow. The regression uses hard-coded offsets for all three
fixtures across resampler caps 1, 3, 8, 32 and 128.

- Python 3.12.5 passed 12 standard-library tests with the GNU Radio case
  skipped. Apple Silicon GNU Radio `g3d33e04` with Python 3.11.7 passed all
  13 tests.
- On that GNU Radio build, 20 CLI sweeps (300 fresh flowgraphs) produced
  byte-identical JSON. The 128-item fixtures each consumed 126 inputs and
  produced 84 outputs. The six-item fixture consumed four and produced three.
  The sink saw inputs 0, 1, 2 and 3 as tags at outputs 0, 1, 1 and 2. The
  two IDs mapped to output 3 were absent, as allowed by the half-open range.
  The comparator unit test injects an observed tag exactly at the excluded
  endpoint and verifies that it is flagged.
- The clean-checkout acceptance commands are the full test suite, the default
  CLI, and `python -m stream_timing --chunk 1 --chunk 3 --chunk 8 --chunk 32 --chunk 128`
  using the GNU Radio interpreter. The default and extended runs must exit 0.
  GitHub Actions runs the same test suite and the default CLI with Ubuntu's
  [GNU Radio package](https://packages.ubuntu.com/noble/gnuradio).
- The first Ubuntu run with GNU Radio 3.10.9.2 returned success from the CLI
  but failed to parse stdout as JSON. The CLI now routes the default runtime
  logger to stderr before loading the bindings. The test exercises this
  behavior with an inherited stdout logger preference.
  [GNU Radio 3.10.9.2 logger](https://github.com/gnuradio/gnuradio/blob/v3.10.9.2/gnuradio-runtime/lib/logger.cc#L29-L56).

The release checks use fixed-rate 2/3 downsampling and a finite offline
source. The original GNU Radio 3.10.8.0 flowgraph linked in issue #7328
was outside this validation. The test results cover the tag IDs and sink
offsets under the scheduler caps listed above.
