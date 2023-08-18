from bloqade.ir.control.waveform import Waveform, Linear, Constant
from typing import Any, List

# this part only for manually build sequences.


def linear(duration, start, stop):
    return Linear(start, stop, duration)


def constant(duration, value):
    return Constant(value, duration)


def piecewise_linear(durations: List[Any], values: List[Any]) -> Waveform:
    pwl_wf = None
    for duration, start, stop in zip(durations, values[:-1], values[1:]):
        if pwl_wf is None:
            pwl_wf = Linear(start, stop, duration)
        else:
            pwl_wf = pwl_wf.append(Linear(start, stop, duration))

    return pwl_wf


def piecewise_constant(durations: List[Any], values: List[Any]) -> Waveform:
    pwc_wf = None
    for duration, value in zip(durations, values):
        if pwc_wf is None:
            pwc_wf = Constant(value, duration)
        else:
            pwc_wf = pwc_wf.append(Constant(value, duration))

    return pwc_wf
