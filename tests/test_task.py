from bloqade.ir.prelude import *
import bloqade.lattice as lattice

seq = Sequence({
    rydberg: {
        detuning: {
            Global: Linear(start=1.0, stop='x', duration=3.0),
            ScaledLocations({1: 1.0, 2: 2.0}): Linear(start=1.0, stop='x', duration=3.0),            
        },
    }
})

print(lattice.Square(3).run(seq).braket(nshots=1000).submit().report().dataframe)
print('bitstring')
print(lattice.Square(3).run(seq).braket(nshots=1000).submit().report().bitstring)

report = lattice.Square(3)\
    .rydberg.detuning.glob\
        .apply(Linear(start=1.0, stop='x', duration=3.0))\
    .location(1).scale(1.0)\
        .apply(Linear(start=1.0, stop='x', duration=3.0))\
    .braket(nshots=1000)\
    .submit(token="wqnknlkwASdsq")\
    .report()
