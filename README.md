# DSP Stream Timing Check

Check whether a fixed-rate DSP stream preserves event IDs and places them at the expected sample indices. The offline GNU Radio adapter runs a 2/3 rational resampler with synthetic I/Q. It requires no radio hardware or recorded signals.

## Timing contract

With interpolation P, decimation Q, and input index n, calculate the exact output position as (nP + delay_ticks − phase_ticks) / Q. The optional phase and delay use ticks of the upsampled sample grid. Round nonnegative positions to the nearest output index, with exact half ties rounded up. Event IDs remain distinct even if their offsets coincide.

The GNU Radio scheduler comparison uses zero phase and zero delay. This checks absolute tag indices. Physical alignment of a filtered waveform can be measured separately with a specified FIR delay and a clear choice of marker. The input offsets near 32 and 64 are fixture coordinates. The actual GNU Radio work-call boundaries depend on the block and scheduler settings.

## Run the reference tests

From the checkout root, run with Python 3.10 or newer.

    python3 -m unittest discover -s tests -v

The reference and comparator use the Python standard library. The suite skips the
GNU Radio integration test when the bindings are absent. All fixture values and
test expectations were authored for this project. For background, see the
[GNU Radio stream tag documentation](https://wiki.gnuradio.org/index.php/Stream_Tags)
and [issue #7328](https://github.com/gnuradio/gnuradio/issues/7328).

## Run the GNU Radio adapter

Use the Python interpreter that loads your GNU Radio installation and PMT.
For example, with the distribution package on Ubuntu 24.04:

```sh
sudo apt install gnuradio
/usr/bin/python3 -c 'from gnuradio import gr, blocks, filter; import pmt; print(gr.version())'
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m stream_timing
/usr/bin/python3 -m stream_timing --fixture finite_boundaries --chunk 1 --chunk 8
```

On macOS or Linux, a separate conda-forge environment is another installation
option. Use that environment's Python for the same commands. See [GNU Radio's
installation guide](https://wiki.gnuradio.org/index.php/InstallingGR).

The adapter sends deterministic synthetic complex I/Q through
`vector_source_c → rational_resampler_ccf → vector_sink_c`. Interpolation is 2,
decimation is 3, and the two real FIR taps are both 1. Event IDs are carried as
PMT symbols under the `event_id` key. Each fixture and chunk setting starts a
fresh headless flowgraph. `--chunk` caps the resampler's `max_noutput_items`.
The scheduler picks the individual work-call sizes. The graph-wide cap is at
least the input vector length to accommodate GNU Radio's tagged source.

The CLI writes JSON to stdout and routes GNU Radio's default logger to stderr.
The report includes the GNU Radio version, scheduler caps, resampler
input consumption, output length, and each event's input, expected, and
observed offsets. The valid output interval is `[0, output_items)`, measured
at the sink after the unpadded source ends. An expected offset at or beyond the
end is marked `outside_output`. Its absence is allowed because that output
item does not exist. An observed event outside the interval fails the check,
even when its offset matches the reference.
Inside the interval each expected ID must occur exactly once at its predicted
offset. Distinct IDs may share an offset, and ordering within an offset is
irrelevant. The report flags missing, unexpected, duplicate, and shifted IDs.
Exit status is 0 for a passing report, 1 for a comparison failure or empty
output, and 2 for invalid CLI arguments or a runtime setup failure.

### Built-in fixtures

| Fixture | Events checked |
| --- | --- |
| `around_input_boundaries` | Inputs 31–33 and 63–65 map to 21, 21, 22, 42, 43, 43 |
| `colliding_output_offsets` | Three distinct IDs at inputs 10, 11, 11 all map to output 7 |
| `finite_boundaries` | Six inputs map to 0, 1, 1, 2, 3, 3. The sink receives three items on the tested runtimes, placing the two tags mapped to 3 outside the valid interval. |

The CLI runs all fixtures at caps 8, 32 and 128 by default. The integration
test also covers caps 1 and 3. The [GitHub Actions workflow](.github/workflows/qa.yml)
shows a clean Ubuntu 24.04 setup and repeats the tests with GNU Radio installed.

[Development notes](DEVELOPMENT.md) record the tested runtime, version-specific
source observations, and limitations.

This project uses the [MIT License](LICENSE).
