# want a function that generates piecewise linear
from typing import Union, List
from bloqade.ir import Linear, Constant

ScalarType = Union[float, str]

# Linear has start, stop, duration values

def piecewise_linear(durations: List[ScalarType], values: List[ScalarType]):
    pwl_wf = None
    for duration, start, stop in zip(durations, values[:-1], values[1:]):
        if pwl_wf is None:
            pwl_wf = Linear(start, stop, duration)
        else:
            pwl_wf = pwl_wf.append(Linear(start, stop, duration))

    return pwl_wf

def piecewise_constant(durations: List[ScalarType], values: List[ScalarType]):
    pwc_wf = None
    for duration, value in zip(durations, values):
        if pwc_wf is None:
            pwc_wf = Constant(value, duration)
        else:
            pwc_wf = pwc_wf.append(Constant(value, duration))

    return pwc_wf

