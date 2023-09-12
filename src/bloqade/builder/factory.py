from bloqade.ir.control.waveform import Waveform, Linear, Constant
from bloqade.builder.typing import ScalarType
from beartype import beartype
from beartype.typing import List

# this part only for manually build sequences.


@beartype
def linear(duration: ScalarType, start: ScalarType, stop: ScalarType):
    return Linear(start, stop, duration)


@beartype
def constant(duration: ScalarType, value: ScalarType):
    return Constant(value, duration)


@beartype
def piecewise_linear(durations: List[ScalarType], values: List[ScalarType]) -> Waveform:
    pwl_wf = None
    for duration, start, stop in zip(durations, values[:-1], values[1:]):
        if pwl_wf is None:
            pwl_wf = Linear(start, stop, duration)
        else:
            pwl_wf = pwl_wf.append(Linear(start, stop, duration))

    return pwl_wf


@beartype
def piecewise_constant(
    durations: List[ScalarType], values: List[ScalarType]
) -> Waveform:
    pwc_wf = None
    for duration, value in zip(durations, values):
        if pwc_wf is None:
            pwc_wf = Constant(value, duration)
        else:
            pwc_wf = pwc_wf.append(Constant(value, duration))

    return pwc_wf
