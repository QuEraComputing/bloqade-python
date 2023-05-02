from bloqade.ir import *
import bloqade.lattice as lattice

# dict interface
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

print(lattice.Square(3).apply(seq).__lattice__)
print(lattice.Square(3).apply(seq).braket(nshots=1000).submit().report().dataframe)
print("bitstring")
print(lattice.Square(3).apply(seq).braket(nshots=1000).submit().report().bitstring)

# pipe interface
report = (
    lattice.Square(3)
    .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
    .location(2)
    .scale(3.0)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
    .hyperfine.rabi.amplitude.location(2)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
    .braket(nshots=1000)
    .submit(token="112312312")
    .report()
)

print(report)
print(report.bitstring)
print(report.dataframe)

lattice.Square(3).rydberg.detuning.location(2).location(3).apply(
    Linear(start=1.0, stop="x", duration=3.0)
).location(3).location(4).apply(Linear(start=1.0, stop="x", duration=3.0)).braket(
    nshots=1000
).submit()

# start.rydberg.detuning.location(2).location(3)


prog = (
    lattice.Square(3)
    .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
    .location(2)
    .scale(3.0)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
    .hyperfine.rabi.amplitude.location(2)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
    .assign(x=1.0)
)
