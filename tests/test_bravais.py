from bloqade.ir.location.bravais import (
    Lieb,
    Square,
    Rectangular,
    Honeycomb,
    Kagome,
    Triangular,
    Chain,
)
from bloqade.ir.location.bravais import Cell
from bloqade import cast
from math import sqrt
from bloqade.compiler.codegen.common.json import BloqadeIRSerializer


def test_square():
    lattice = Square(3, lattice_spacing=2.0)

    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast([(0, 0), (0, 2), (0, 4), (2, 0), (2, 2), (2, 4), (4, 0), (4, 2), (4, 4)])
    )

    assert positions == positions_expected


def test_rectangular():
    lattice = Rectangular(2, 3, lattice_spacing_x=0.5, lattice_spacing_y=2)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast([(0, 0), (0, 2.0), (0, 4.0), (0.5, 0), (0.5, 2.0), (0.5, 4.0)])
    )
    assert positions == positions_expected


def test_rectagnular_default_yscale():
    lattice = Rectangular(2, 3, lattice_spacing_x=0.5)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast([(0, 0), (0, 1.0), (0, 2.0), (0.5, 0), (0.5, 1.0), (0.5, 2.0)])
    )
    assert positions == positions_expected


def test_kagome():
    lattice = Kagome(2, lattice_spacing=2.0)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast(
            [
                (0, 0),
                (1.0, 0),
                (2, 0),
                (3, 0),
                (0.5, sqrt(3) * 0.5),
                (2.5, sqrt(3) * 0.5),
                (1, sqrt(3)),
                (3, sqrt(3)),
                (2, sqrt(3)),
                (4, sqrt(3)),
                (1.5, sqrt(3) * 1.5),
                (3.5, sqrt(3) * 1.5),
            ]
        )
    )

    assert positions == positions_expected


def test_triangular():
    lattice = Triangular(2, lattice_spacing=2.0)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(cast([(0, 0), (2, 0), (1.0, sqrt(3)), (3, sqrt(3))]))

    assert positions == positions_expected


def test_honeycomb():
    lattice = Honeycomb(2, lattice_spacing=2)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast(
            [
                (0.0, 0),
                (2.0, 0),
                (1.0, 1 / sqrt(3)),
                (3.0, 1 / sqrt(3)),
                (1.0, sqrt(3)),
                (3.0, sqrt(3)),
                (2.0, sqrt(3) + 1 / sqrt(3)),
                (4.0, sqrt(3) + 1 / sqrt(3)),
            ]
        )
    )

    assert positions == positions_expected
    assert lattice.n_dims == 2


def test_lieb():
    lattice = Lieb(2, lattice_spacing=2)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast(
            [
                (0, 0),
                (2, 0),
                (0, 2),
                (2, 2),
                (1, 0),
                (3, 0),
                (1, 2),
                (3, 2),
                (0, 1),
                (2, 1),
                (0, 3),
                (2, 3),
            ]
        )
    )

    assert positions == positions_expected
    assert lattice.n_dims == 2


def test_scale_lattice():
    lattice = Triangular(2, lattice_spacing=1)
    latt2 = lattice.scale(2)
    positions = set(map(lambda info: info.position, latt2.enumerate()))
    positions_expected = set(cast([(0, 0), (2, 0), (1.0, sqrt(3)), (3, sqrt(3))]))

    assert positions == positions_expected
    assert lattice.n_dims == 2


def test_chain():
    lattice = Chain(4, lattice_spacing=1, vertical_chain=False)
    latt2 = lattice.scale(2)
    positions = set(map(lambda info: info.position, latt2.enumerate()))
    positions_expected = set(cast([(0, 0), (2, 0), (4, 0), (6, 0)]))

    assert positions == positions_expected
    assert lattice.n_dims == 1

    vertical_lattice = Chain(4, lattice_spacing=1, vertical_chain=True)
    positions = set(map(lambda info: info.position, vertical_lattice.enumerate()))
    positions_expected = set(cast([(0, 0), (0, 1), (0, 2), (0, 3)]))

    assert positions == positions_expected
    assert vertical_lattice.n_dims == 1

    lattice_dict = BloqadeIRSerializer().default(vertical_lattice)

    assert lattice_dict["chain"]["L"] == 4
    assert lattice_dict["chain"]["vertical_chain"] is True
    assert lattice_dict["chain"]["lattice_spacing"] == {"literal": {"value": "1"}}

    assert lattice_dict


def test_cell():
    c = Cell(10, 2)

    assert c.natoms == 10
    assert c.ndims == 2
