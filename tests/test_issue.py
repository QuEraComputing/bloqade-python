from bloqade.ir.prelude import *
import bloqade.lattice as lattice

(   
    lattice.Square(3)
        .rydberg.detuning.glob.apply(Linear(start=1.0, stop="x", duration=3.0))
        .location(2)
        .scale(3.0)
        .apply(Linear(start=1.0, stop="x", duration=3.0))
)

(
    lattice.Square(3)
        .rydberg.detuning.glob.apply(Linear(start=1.0, stop="x", duration=3.0))
        .location(2)
        .scale(3.0)
        .apply(Linear(start=1.0, stop="x", duration=3.0))
)
