# DSP Stream Timing Check

A small test project for checking event IDs and sample offsets through a fixed-rate DSP stream. The initial fixtures use a 2/3 rational resampler and synthetic samples. They exercise events near sample indices that can coincide with block boundaries and several distinct events that land on one output item.

## Timing contract

With interpolation P, decimation Q, and input index n, calculate the exact output position as (nP + delay_ticks − phase_ticks) / Q. The optional phase and delay use ticks of the upsampled sample grid. Round nonnegative positions to the nearest output index, with exact half ties rounded up. Event IDs remain distinct even if their offsets coincide.

The GNU Radio scheduler comparison uses zero phase and zero delay. This checks absolute tag indices. Physical alignment of a filtered waveform can be measured separately with a specified FIR delay and a clear choice of marker. The input offsets near 32 and 64 are fixture coordinates. The actual GNU Radio work-call boundaries depend on the block and scheduler settings.

## Run the reference tests

Run with Python 3.10 or newer.

    python3 -m unittest discover -s tests -v

The reference uses the Python standard library. The fixture values and test expectations are authored for this project. [GNU Radio stream tag documentation](https://wiki.gnuradio.org/index.php/Stream_Tags) and [issue #7328](https://github.com/gnuradio/gnuradio/issues/7328) describe the interoperability target and related historical report.
