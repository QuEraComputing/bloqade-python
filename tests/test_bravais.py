from bloqade.ir.location import Square, Rectangular, Honeycomb
from bloqade import cast
import pytest


#@pytest.mark.skipif(True, reason="Not implemented")
def test_square():
    lattice = Square(3, lattice_spacing=2.0)

    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast([(0, 0), (0, 2), (0, 4), (2, 0), (2, 2), (2, 4), (4, 0), (4, 2), (4, 4)])
    )

    assert positions == positions_expected


#@pytest.mark.skipif(True, reason="Not implemented")
def test_rectangular():
    lattice = Rectangular(2, 3, lattice_sapcing_x=0.5, lattice_spacing_y=2)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast([(0, 0), (0, 2.0), (0, 4.0), (0.5, 0), (0.5, 2.0), (0.5, 4.0)])
    )
    assert positions == positions_expected


#@pytest.mark.skipif(True, reason="Not implemented")
def test_honeycomb():
    lattice = Honeycomb(3,lattice_spacing=2)
    positions = set(map(lambda info: info.position, lattice.enumerate()))
    positions_expected = set(
        cast(
            [
                (0, 0),
                (0, 2),
                (0, 4),
                (2, 0),
                (2, 2),
                (2, 4),
                (4, 0),
                (4, 2),
                (4, 4),
                (6, 0),
                (6, 2),
                (6, 4),
                (8, 0),
                (8, 2),
                (8, 4),
            ]
        )
    )

    assert positions == positions_expected
