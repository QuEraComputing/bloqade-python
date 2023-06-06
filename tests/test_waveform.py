from bloqade.ir import (
    Linear,
    Constant,
    Poly,
    Record,
    AlignedWaveform,
    Alignment,
    AlignedValue,
    instruction,
)
from bloqade.ir import scalar

wf = Linear(start=1.0, stop="x", duration=3.0)
wf = Constant(value=1.0, duration=3.0)


@instruction(duration="r")
def my_func(time, *, omega, phi=0, amplitude):
    import numpy as np

    return amplitude * np.cos(omega * time + phi)


print(wf[:0.5].duration)
print(wf[1.0:].duration)
print(wf[0.2:0.8].duration)

print(-wf)
print(wf.scale(1.0))

eval(repr(-wf))
eval(repr(wf.scale(1.0)))

# canonicalize append
wf = (
    Linear(0.0, "rabi_amplitude_max", "up_time")
    .append(Constant("rabi_amplitude_max", "anneal_time"))
    .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
)
print(wf)

smooth_wf = wf.smooth(0.1, "gaussian")
print(smooth_wf(1.0, rabi_amplitude_max=1.0, up_time=1.0, anneal_time=1.0))
smooth_wf = wf.smooth(0.1, "biweight")
print(smooth_wf(1.0, rabi_amplitude_max=1.0, up_time=1.0, anneal_time=1.0))

# try scaling
wf * scalar.Literal(5.0)

# try addition
wf + wf

# polynomial
Poly(
    [scalar.Literal(10) + scalar.Variable("l"), scalar.Literal(5), scalar.Literal(-2)],
    scalar.Variable("g"),
)

# Record
Record(wf, scalar.Variable("n"))

AlignedWaveform(wf, Alignment.Left, AlignedValue.Right)

# eval(repr(wf))

# print(wf)

# wf = wf.append(wf)
# eval(repr(wf))
# print(wf)

# wf = Linear(0.0, "rabi_amplitude_max", "up_time").append(wf)
# eval(repr(wf))
# print(wf)
