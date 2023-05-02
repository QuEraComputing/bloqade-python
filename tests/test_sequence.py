from bloqade.ir.prelude import *

print(rydberg)

f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})

print(Pulse({detuning: f}))
print(Pulse({rabi.amplitude: f}))
print(Pulse({rabi.phase: f}))

pulse = Pulse({detuning: {Uniform: Linear(start=1.0, stop="x", duration=3.0)}})


seq = Sequence(
    {
        rydberg: {
            detuning: {
                Uniform: Linear(start=1.0, stop="x", duration=3.0),
                ScaledLocations({1: 1.0, 2: 2.0}): Linear(
                    start=1.0, stop="x", duration=3.0
                ),
            },
        }
    }
)

print(seq)
print(seq.name("test"))
print(seq.append(seq))
print(seq[:0.5])
