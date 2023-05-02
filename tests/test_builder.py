from bloqade.builder import *
from bloqade.ir import *

wf = Linear(start=1.0, stop="x", duration=3.0)

seq = Start().rydberg.rabi.amplitude\
    .location(1).linear(start=1.0, stop=2.0, duration='x')\
    .location(2).linear(start=1.0, stop=2.0, duration='x').constant(1.0, 3.0)\
    .uniform.linear(start=1.0, stop=2.0, duration='x')\
    .sequence

seq = Start().rydberg.rabi.amplitude\
    .uniform.apply(Linear(start=1.0, stop=2.0, duration='x'))\
    .location(1).linear(start=1.0, stop=2.0, duration='x')\
    .program

print(seq.seq)
print(seq.lattice)
print(seq.assignments)
