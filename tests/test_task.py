from bloqade.ir.prelude import *
import bloqade.ir.lattice as lattice

seq = Sequence({
    rydberg: {
        detuning: {
            Global: Linear(start=1.0, stop='x', duration=3.0),
            ScaledLocations({1: 1.0, 2: 2.0}): Linear(start=1.0, stop='x', duration=3.0),            
        },
    }
})

print(lattice.square((3, 3)).run(seq).braket(nshots=1000).submit().report().dataframe)
print('bitstring')
print(lattice.square((3, 3)).run(seq).braket(nshots=1000).submit().report().bitstring)
