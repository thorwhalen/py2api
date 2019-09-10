"""
    http://0.0.0.0:5000/?attr=timed_sines
    http://0.0.0.0:5000/?attr=get_data_chunk
    http://0.0.0.0:5000/?attr=get_data_chunk&n=5
    http://0.0.0.0:5000/?attr=get_data_chunk&n=5&freq=100&amplitude=9.9&phase_in_radians=3.14
"""

import time
from math import pi
import numpy as np
import matplotlib.pylab as plt
import pandas as pd

DFLT_N = 60
DFLT_FREQ = 440
DFLT_AMPLITUDE = 1
DFLT_PHASE = 0
DFLT_SR = 1000


def test_func(df: pd.DataFrame, x: int = 1):
    return df.sum() * x  # does the stuff


def timed_sines(freq=DFLT_FREQ, amplitude=DFLT_AMPLITUDE, phase_in_radians=DFLT_PHASE):
    """Get the (timestamp, sine_wave_value) point (of an underlying sine waveform)

    Args:
        freq: The frequency of the sine wave
        amplitude: Amplitude of
        phase_in_radians: Phase in radians

    Returns:
        A (ts, val) point where ts is a UTC timestamp (in seconds) and val is a sample of a waveform at that time.
    """
    t = time.time()

    y = np.sin(phase_in_radians + 2 * pi * freq * t) * amplitude
    return t, y


def get_data_chunk(n=DFLT_N, sr=DFLT_SR, freq=DFLT_FREQ, amplitude=DFLT_AMPLITUDE, phase_in_radians=DFLT_PHASE):
    """Return a list of (ts, val) where ts is a UTC seconds timestamp and val is the value of a sine wave at that time

    Args:
        n: The number of data points you want
        sr: The (approximate, and lower bound) rate at which you want to sample the requested points (in samples per s)
        freq: The frequency of the sine wave
        amplitude: Amplitude of
        phase_in_radians: Phase in radians

    Returns:
        A list of (ts, val) pairs
    """
    chunk = list()
    for _ in range(n):
        time.sleep(1 / sr)  # TODO: computer sample rate more precisely, with cumulative loop speed
        chunk.append(timed_sines(freq, amplitude, phase_in_radians))
    return chunk


def _plot_sine_samples(n=DFLT_N, sr=DFLT_SR, freq=DFLT_FREQ, amplitude=DFLT_AMPLITUDE, phase_in_radians=DFLT_PHASE):
    offset = time.time()
    chunk = get_data_chunk(n=n, sr=sr, freq=freq, amplitude=amplitude, phase_in_radians=phase_in_radians)
    ts, ys = list(zip(*chunk))
    return plt.plot(np.array(ts) - offset, ys, '-o')


if __name__ == "__main__":
    from flask import jsonify
    from py2api.py2rest.obj_wrap import WebObjWrapper
    from py2api.py2rest.input_trans import InputTrans, _ARGNAME, _ELSE
    from py2api.output_trans import OutputTrans, _ATTR
    from py2api.py2rest.app_maker import mk_app, dflt_run_app_kwargs

    import sys

    input_trans = InputTrans(
        trans_spec={
            _ARGNAME: {  # these argument can all be floats (don't have to be handled differently)
                'n': int,
                'freq': int,
                'sr': int,
                'amplitude': float,
                'phase_in_radians': float,
                'df': pd.DataFrame
            }
        })

    output_trans = OutputTrans(
        trans_spec={
            _ATTR: {
                'test_func': lambda x: jsonify({'_result': x.to_dict()})
            },
            _ELSE: lambda x: jsonify({'_result': x})}
    )

    wrap = WebObjWrapper(obj_constructor=sys.modules[__name__],  # wrap this current module
                         obj_constructor_arg_names=[],  # no construction, so no construction args
                         permissible_attr=['timed_sines', 'get_data_chunk', 'test_func'],
                         input_trans=input_trans,
                         output_trans=output_trans,
                         name='/',
                         debug=0)

    app = mk_app(app_name=__name__, routes=[wrap])

    app.run(**dflt_run_app_kwargs())
