from bloqade.ir import Linear
import bloqade.atoms as atoms

(
    atoms.Square(3)
    .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
    .location(2)
    .scale(3.0)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
)

(
    atoms.Square(3)
    .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
    .location(2)
    .scale(3.0)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
)
