from .location import AtomArrangement, ParallelRegister, LocationInfo, ListOfLocations
from .bravais import (
    BoundedBravais,
    Chain,
    Square,
    Rectangular,
    Honeycomb,
    Triangular,
    Lieb,
    Kagome,
)


start = ListOfLocations()
"""
A Program starting point, alias of empty
[`ListOfLocations`][bloqade.ir.location.list.ListOfLocations].

- Next possible steps to build your program are:
- Specify which level coupling to address with:
    - `start.rydberg`: for [`Rydberg`][bloqade.builder.coupling.Rydberg]
        Level coupling
    - `start.hyperfine`: for [`Hyperfine`][bloqade.builder.coupling.Hyperfine]
        Level coupling
    - LOCKOUT: You cannot add atoms to your geometry after specifying level coupling.
- continue/start building your geometry with:
    - `start.add_position()`: to add atom(s) to current register. It will accept:
        - A single coordinate, represented as a tuple (e.g. `(5,6)`) with a value that
          can either be:
            - integers: `(5,6)`
            - floats: `(5.1, 2.5)`
            - strings (for later variable assignment): `("x", "y")`
            - [`Scalar`][bloqade.ir.scalar.Scalar] objects: `(2*cast("x"), 5+cast("y"))`
        - A list of coordinates, represented as a list of types mentioned previously.
        - A numpy array with shape (n, 2) where n is the total number of atoms
"""


__all__ = [
    "start",
    "AtomArrangement",
    "Chain",
    "Square",
    "Rectangular",
    "Honeycomb",
    "Triangular",
    "Lieb",
    "Kagome",
    "BoundedBravais",
    "ListOfLocations",
    "ParallelRegister",
    "LocationInfo",
]
