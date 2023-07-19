import bloqade.ir as ir
from bloqade.ir.location import ListOfLocations, AtomArrangement
from bloqade.ir.location import Square
from bloqade import cast
import pytest


def test_listOfLocatoions():
    lattice = ListOfLocations(
        [(0, 0), (0, 1), (1, 0), (1, 1)]
    )  # enumerate method gives a generator that can be taken advantage of

    positions1 = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast(
            [
                (0, 0),
                (1, 0),
                (0, 1),
                (1, 1),
            ]
        )
    )
    assert positions1 == positions_expected

    # scale:
    lattice = lattice.scale(3.2)

    positions1 = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast(
            [
                (0, 0),
                (3.2, 0),
                (0, 3.2),
                (3.2, 3.2),
            ]
        )
    )
    assert positions1 == positions_expected


def test_addlocs_on_square():
    lattice = Square(2, lattice_spacing=1.0)
    lattice1 = lattice.add_positions([(9, 6), (4, 4)])

    # type(lattice)
    assert type(lattice1) == ir.location.ListOfLocations

    positions1 = set(map(lambda info: info.position, lattice1.enumerate()))
    positions_expected1 = set(cast([(0, 0), (1, 0), (0, 1), (1, 1), (9, 6), (4, 4)]))

    assert positions1 == positions_expected1


def test_addlocs_filling_options():
    lattice = Square(2, lattice_spacing=1.0)
    lattice = lattice.add_positions([(9, 6), (4, 4)], filling=[False, True])

    # type(lattice)
    assert type(lattice) == ir.location.ListOfLocations

    for info in lattice.enumerate():
        if info.position == cast((9, 6)):
            assert bool(info.filling) is False
        else:
            assert bool(info.filling) is True

    assert lattice.n_dims == 2


def test_internal_base_listofloc():
    lattice = AtomArrangement()

    with pytest.raises(NotImplementedError):
        set(map(lambda info: info.position, lattice.enumerate()))

    with pytest.raises(NotImplementedError):
        lattice.n_atoms

    with pytest.raises(NotImplementedError):
        lattice.n_dims
