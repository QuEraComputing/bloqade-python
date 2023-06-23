from bloqade.ir import Linear
from bloqade import start

wf = Linear(start=1.0, stop="x", duration=3.0)

seq = (
    start.rydberg.rabi.amplitude.location(1)
    .linear(start=1.0, stop=2.0, duration="x")
    .location(2)
    .linear(start=1.0, stop=2.0, duration="x")
    .constant(1.0, 3.0)
    .uniform.linear(start=1.0, stop=2.0, duration="x")
    .sequence
)

seq = (
    start.rydberg.rabi.amplitude.uniform.apply(
        Linear(start=1.0, stop=2.0, duration="x")
    )
    .location(1)
    .linear(start=1.0, stop=2.0, duration="x")
    .sequence
)

# print(seq.seq)
# print(seq.lattice)
# print(seq.assignments)
