from bloqade.ir import Sequence, rydberg, detuning, Uniform, Linear, ScaledLocations
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
    .multiplex.braket(nshots=1000)
    .submit()
    .report()
    .dataframe.groupby(by=["x"])
    .count()
)

(
    lattice.Square(3)
    .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
    .multiplex.quera
)


wf = (
    Linear(start=1.0, stop=2.0, duration=2.0)
    .scale(2.0)
    .append(Linear(start=1.0, stop=2.0, duration=2.0))
)


prog = (
    lattice.Square(3)
    .hyperfine.detuning.location(1)
    .scale(2.0)
    .piecewise_linear(coeffs=[1.0, 2.0, 3.0])
    .location(2)
    .constant(value=2.0, duration="x")
)

prog.seq
prog.lattice
