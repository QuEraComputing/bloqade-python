import bloqade.ir as ir
from bloqade.ir.location import ListOfLocations, AtomArrangement
from bloqade.ir.location import Square
from bloqade.constants import RB_C6
from bloqade import cast
import pytest
import numpy as np


def test_rydberg_interactions():
    geometry = ListOfLocations([(0, 0), (1, 0), (0, 1), (1, 1)]).scale(5.0)

    V_ij = geometry.rydberg_interaction()

    # 2  3
    #  \/
    #  /\
    # 0  1

    d_01 = 5.0
    d_02 = 5.0
    d_03 = np.sqrt(2) * 5.0
    d_12 = np.sqrt(2) * 5.0
    d_13 = 5.0
    d_23 = 5.0

    V_01 = RB_C6 / d_01**6
    V_02 = RB_C6 / d_02**6
    V_03 = RB_C6 / d_03**6
    V_12 = RB_C6 / d_12**6
    V_13 = RB_C6 / d_13**6
    V_23 = RB_C6 / d_23**6

    V_ij_expected = np.array(
        [[0, 0, 0, 0], [V_01, 0, 0, 0], [V_02, V_12, 0, 0], [V_03, V_13, V_23, 0]]
    )

    assert np.allclose(V_ij, V_ij_expected)


def test_listOfLocations():
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
    lattice1 = lattice.add_position([(9, 6), (4, 4)])

    # type(lattice)
    assert type(lattice1) == ir.location.ListOfLocations

    positions1 = set(map(lambda info: info.position, lattice1.enumerate()))
    positions_expected1 = set(cast([(0, 0), (1, 0), (0, 1), (1, 1), (9, 6), (4, 4)]))

    assert positions1 == positions_expected1


def test_addlocs_filling_options():
    lattice = Square(2, lattice_spacing=1.0)
    lattice = lattice.add_position([(9, 6), (4, 4)], filling=[False, True])

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
