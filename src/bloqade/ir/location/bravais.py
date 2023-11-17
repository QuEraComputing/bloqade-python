from functools import cached_property
from pydantic.dataclasses import dataclass
from dataclasses import fields
import numpy as np
import itertools
from numpy.typing import NDArray
from bloqade.ir.location.base import AtomArrangement, LocationInfo
from bloqade.ir import Literal, Scalar, cast

from bloqade.builder.typing import ScalarType
from beartype.typing import List, Tuple, Generator, Optional
from beartype import beartype

import plotext as pltxt
import sys


class Cell:
    @beartype
    def __init__(self, natoms: int, ndims: int) -> None:
        self.natoms = natoms
        self.ndims = ndims


@dataclass
class BoundedBravais(AtomArrangement):
    __match_args__ = ("shape", "lattice_spacing")
    """Base classe for Bravais lattices
    [`AtomArrangement`][bloqade.ir.location.base.AtomArrangement].

    - [`Square`][bloqade.ir.location.bravais.Square]
    - [`Chain`][bloqade.ir.location.bravais.Chain]
    - [`Honeycomb`][bloqade.ir.location.bravais.Honeycomb]
    - [`Triangular`][bloqade.ir.location.bravais.Triangular]
    - [`Lieb`][bloqade.ir.location.bravais.Lieb]
    - [`Kagome`][bloqade.ir.location.bravais.Kagome]
    - [`Rectangular`][bloqade.ir.location.bravais.Rectangular]


    """

    def cell_vectors(self) -> Tuple[Tuple[Scalar, ...], ...]:
        raise NotImplementedError

    def cell_atoms(self) -> Tuple[Tuple[Scalar, ...], ...]:
        raise NotImplementedError

    def __str__(self):
        has_lattice_spacing_var = False
        if type(self.lattice_spacing) is not Literal:
            # add string denoting this to printer
            repr_lattice_spacing = 1.0
            has_lattice_spacing_var = True
        else:
            repr_lattice_spacing = float(self.lattice_spacing.value)

        xs, ys = [], []

        for index in itertools.product(*[range(n) for n in self.shape]):
            for pos in self.coordinates(list(index)):
                (x, y) = tuple(repr_lattice_spacing * pos)
                xs.append(x)
                ys.append(y)

        pltxt.clear_figure()
        pltxt.limit_size(False, False)
        pltxt.plot_size(80, 24)
        pltxt.canvas_color("default")
        pltxt.axes_color("default")
        pltxt.ticks_color("white")
        pltxt.title("Atom Positions")
        pltxt.xlabel("x (um)")
        pltxt.ylabel("y (um)")
        if has_lattice_spacing_var:
            pltxt.ylabel(
                "Lattice Spacing is a variable, defaulting to 1.0 for display", "right"
            )

        marker = "."
        if sys.stdout.encoding.lower().startswith("utf"):
            marker = "dot"

        pltxt.scatter(xs, ys, color=(100, 55, 255), marker=marker)

        return pltxt.build()

    @property
    def shape(self) -> Tuple[int, ...]:
        raise NotImplementedError("shape is not implemented")

    @cached_property
    def n_atoms(self) -> int:
        return len(self.cell_atoms()) * np.prod(self.shape)

    @property
    def n_sites(self) -> int:
        return self.n_atoms

    @property
    def n_vacant(self) -> int:
        return 0

    @property
    def n_dims(self):
        """dimension of the lattice

        Returns:
            int: dimension of the lattice

        """
        return len(self.cell_vectors())

    @beartype
    def coordinates(self, index: List[int]) -> NDArray:
        """calculate the coordinates of a cell in the lattice
        given the cell index.
        """
        # damn! this is like stone age broadcasting
        vectors = np.array(self.cell_vectors())
        index = np.array(index)
        pos = np.sum(vectors.T * index, axis=1)
        return pos + np.array(self.cell_atoms())

    def enumerate(self) -> Generator[LocationInfo, None, None]:
        for index in itertools.product(*[range(n) for n in self.shape]):
            for pos in self.coordinates(list(index)):
                position = tuple(self.lattice_spacing * pos)
                yield LocationInfo.create(position, True)

    def __iter__(self):
        for index in itertools.product(*[range(n) for n in self.shape]):
            for pos in self.coordinates(list(index)):
                position = tuple(self.lattice_spacing * pos)
                yield LocationInfo.create(position, True)

    @beartype
    def scale(self, factor: ScalarType) -> "BoundedBravais":
        """Scale the current location with a factor.

        (x,y) -> factor*(x,y)

        Args:
            factor (str | Real | Decimal | Scalar): scale factor

        Returns:
            BoundedBravais: The lattice with the scaled locations
        """
        factor = cast(factor)
        obj = self.__new__(type(self))
        for f in fields(self):
            if f.name == "lattice_spacing":
                obj.lattice_spacing = factor * self.lattice_spacing
            else:
                setattr(obj, f.name, getattr(self, f.name))
        return obj


@dataclass(init=False)
class Chain(BoundedBravais):
    """Chain lattice.

    - 1D lattice
    - primitive (cell) vector(s)
        - a1 = (1,0).
    - unit cell (1 atom(s))
        - loc (0,0)

    Args:
        L (int): number of sites in the chain
        lattice_spacing (Scalar, Real): lattice spacing. Defaults to 1.0.


    - Possible Next:
        continue with `.` to see possible next step in auto-prompt
        supported setting (IPython, IDE ...)

    """

    L: int
    lattice_spacing: Scalar
    vertical_chain: bool

    def __init__(
        self, L: int, lattice_spacing: ScalarType = 1.0, vertical_chain: bool = False
    ):
        self.L = L
        self.lattice_spacing = cast(lattice_spacing)
        self.vertical_chain = vertical_chain
        super().__init__()

    def __repr__(self):
        return super().__repr__()

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.L,)

    def cell_vectors(self) -> List[List[float]]:
        if self.vertical_chain:
            return [[0, 1]]
        else:
            return [[1, 0]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]


@dataclass
class Square(BoundedBravais):
    """Square lattice.

    - 2D lattice
    - primitive (cell) vector(s)
        - a1 = (1,0)
        - a2 = (0,1)
    - unit cell (1 atom(s))
        - loc (0,0)

    Args:
        L1 (int): number of sites in linear direction. n_atoms = L1 * L1.
        L2 (Optional[int]): number of sites in direction a2.
            n_atoms = L1 * L2, default is L1
        lattice_spacing (Scalar, Real): lattice spacing. Defaults to 1.0.


    - Possible Next:
        continue with `.` to see possible next step in auto-prompt
        supported setting (IPython, IDE ...)

    """

    L1: int
    L2: int
    lattice_spacing: Scalar

    def __init__(
        self, L1: int, L2: Optional[int] = None, lattice_spacing: ScalarType = 1.0
    ):
        if L2 is None:
            L2 = L1
        self.L1 = L1
        self.L2 = L2
        self.lattice_spacing = cast(lattice_spacing)
        super().__init__()

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.L1, self.L2)

    def __repr__(self):
        return super().__repr__()

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, 1]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]


@dataclass(init=False)
class Rectangular(BoundedBravais):
    """Rectangular lattice.

    - 2D lattice
    - primitive (cell) vector(s)
        - a1 = (1,0)
        - a2 = (0,1)
    - unit cell (1 atom(s))
        - loc (0,0)


    Args:
        width (int): number of sites in x direction.
        height (int): number of sites in y direction.
        lattice_spacing_x (Scalar, Real):
            lattice spacing. Defaults to 1.0.
        lattice_spacing_y (Scalar, Real):
            lattice spacing in y direction. optional.


    - Possible Next:
        continue with `.` to see possible next step in auto-prompt
        supported setting (IPython, IDE ...)

    """

    width: int
    height: int
    lattice_spacing_x: Scalar
    lattice_spacing_y: Scalar

    def __init__(
        self,
        width: int,
        height: int,
        lattice_spacing_x: ScalarType = 1.0,
        lattice_spacing_y: ScalarType = 1.0,
    ):
        self.width = width
        self.height = height
        self.lattice_spacing_x = cast(lattice_spacing_x)
        self.lattice_spacing_y = (
            cast(lattice_spacing_y)
            if lattice_spacing_y is not None
            else self.lattice_spacing_x
        )

        super().__init__()

    def __str__(self):
        # modified version of the standard coordinates method,
        # intercept cell.vectors, then continue with standard
        # operation
        def repr_compatible_coordinates(self, index: List[int]) -> NDArray:
            cell_vectors = self.cell_vectors()
            cell_vectors[1][1] = float(cell_vectors[1][1].value)

            vectors = np.array(cell_vectors)
            index = np.array(index)
            pos = np.sum(vectors.T * index, axis=1)
            return pos + np.array(self.cell_atoms())

        # if ratio is a Literal, then
        # by extension the lattice_spacing must also be a Literal
        if isinstance(self.lattice_spacing_x, Literal) and isinstance(
            self.lattice_spacing_y, Literal
        ):
            repr_lattice_spacing = float(self.lattice_spacing.value)

            xs, ys = [], []

            for index in itertools.product(*[range(n) for n in self.shape]):
                for pos in repr_compatible_coordinates(
                    self, index
                ):  # need to replace this
                    (x, y) = tuple(repr_lattice_spacing * pos)
                    xs.append(x)
                    ys.append(y)

            pltxt.clear_figure()
            pltxt.limit_size(False, False)
            pltxt.plot_size(80, 24)
            pltxt.canvas_color("default")
            pltxt.axes_color("default")
            pltxt.ticks_color("white")
            pltxt.title("Atom Positions")
            pltxt.xlabel("x (um)")
            pltxt.ylabel("y (um)")

            marker = "."
            if sys.stdout.encoding.lower().startswith("utf"):
                marker = "dot"

            pltxt.scatter(xs, ys, color=(100, 55, 255), marker=marker)

            return pltxt.build()

        else:
            return "Rectangular(shape={}, lattice_spacing={}, ratio={})".format(
                self.shape, self.lattice_spacing, self.ratio
            )

    @property
    def lattice_spacing(self) -> Scalar:
        return self.lattice_spacing_x

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.width, self.height)

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, self.lattice_spacing_y / self.lattice_spacing_x]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]


@dataclass
class Honeycomb(BoundedBravais):
    """Honeycomb lattice.

    - 2D lattice
    - primitive (cell) vector(s)
        - a1 = (1, 0)
        - a2 = (1/2, sqrt(3)/2)
    - unit cell (2 atom(s))
        - loc1 (0, 0)
        - loc2 (1/2, 1/(2*sqrt(3))


    Args:
        L1 (int): number of unit cells in linear direction. n_atoms = L1 * L1 * 2.
        L2 (Optional[int]): number of unit cells in direction a2.
            n_atoms = L1 * L2 * 2, default is L1.

        lattice_spacing (Scalar, Real):
            lattice spacing. Defaults to 1.0.


    - Possible Next:
        continue with `.` to see possible next step in auto-prompt
        supported setting (IPython, IDE ...)

    """

    L1: int
    L2: int
    lattice_spacing: Scalar

    @beartype
    def __init__(
        self, L1: int, L2: Optional[int] = None, lattice_spacing: ScalarType = 1.0
    ):
        if L2 is None:
            L2 = L1

        self.L1 = L1
        self.L2 = L2
        self.lattice_spacing = cast(lattice_spacing)

        super().__init__()

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.L1, self.L2)

    def __repr__(self):
        return super().__repr__()

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, 1 / (2 * np.sqrt(3))]]


@dataclass
class Triangular(BoundedBravais):
    """Triangular lattice.

    - 2D lattice
    - primitive (cell) vector(s)
        - a1 = (1, 0)
        - a2 = (1/2, sqrt(3)/2)
    - unit cell (1 atom(s))
        - loc (0, 0)


    Args:
        L (int): number of sites in linear direction. n_atoms = L * L.
        L2 (Optional[int]): number of sites along a2 direction,
            n_atoms = L1 * L2, default is L1.
        lattice_spacing (Scalar, Real):
            lattice spacing. Defaults to 1.0.


    - Possible Next:
        continue with `.` to see possible next step in auto-prompt
        supported setting (IPython, IDE ...)

    """

    L1: int
    L2: int
    lattice_spacing: Scalar

    @beartype
    def __init__(
        self, L1: int, L2: Optional[int] = None, lattice_spacing: ScalarType = 1.0
    ):
        if L2 is None:
            L2 = L1
        self.L1 = L1
        self.L2 = L2
        self.lattice_spacing = cast(lattice_spacing)

        super().__init__()

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.L1, self.L2)

    def __repr__(self):
        return super().__repr__()

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0]]


@dataclass
class Lieb(BoundedBravais):
    """Lieb lattice.

    - 2D lattice
    - primitive (cell) vector(s)
        - a1 = (1, 0)
        - a2 = (0, 1)
    - unit cell (3 atom(s))
        - loc1 (0, 0)
        - loc2 (0.5, 0)
        - loc3 (0 ,0.5)

    Args:
        L1 (int): number of unit cells in linear direction. n_atoms = 3* L1 * L1.
        L2 (Optional[int]): number of unit cells along a2 direction,
            n_atoms = 3 * L1 * L2, default is L1.
        lattice_spacing (Scalar, Real):
            lattice spacing. Defaults to 1.0.


    - Possible Next:
        continue with `.` to see possible next step in auto-prompt
        supported setting (IPython, IDE ...)

    """

    L1: int
    L2: int
    lattice_spacing: Scalar

    @beartype
    def __init__(
        self, L1: int, L2: Optional[int] = None, lattice_spacing: ScalarType = 1.0
    ):
        if L2 is None:
            L2 = L1
        self.L1 = L1
        self.L2 = L2
        self.lattice_spacing = cast(lattice_spacing)

    def __repr__(self):
        return super().__repr__()

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [0.0, 1.0]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, 0.0], [0.0, 1 / 2]]

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.L1, self.L2)


@dataclass
class Kagome(BoundedBravais):
    """Kagome lattice.

    - 2D lattice
    - primitive (cell) vector(s)
        - a1 = (1, 0)
        - a2 = (1/2, sqrt(3)/2)
    - unit cell (3 atom(s))
        - loc1 (0, 0)
        - loc2 (0.5, 0)
        - loc3 (0.25 ,0.25sqrt(3))

    Args:
        L1 (int): number of sites in linear direction. n_atoms = 3 * L1 * L1.
        L2 (Optional[int]): number of unit cells along a2 direction,
            n_atoms = 3 * L1 * L2, default is L1.
        lattice_spacing (Scalar, Real):
            lattice spacing. Defaults to 1.0.


    - Possible Next:
        continue with `.` to see possible next step in auto-prompt
        supported setting (IPython, IDE ...)

    """

    L1: int
    L2: int
    lattice_spacing: Scalar

    @beartype
    def __init__(
        self, L1: int, L2: Optional[int] = None, lattice_spacing: ScalarType = 1.0
    ):
        if L2 is None:
            L2 = L1

        self.L1 = L1
        self.L2 = L2
        self.lattice_spacing = cast(lattice_spacing)
        super().__init__()

    @property
    def shape(self) -> Tuple[int, ...]:
        return (self.L1, self.L2)

    def __repr__(self):
        return super().__repr__()

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, 0], [1 / 4, np.sqrt(3) / 4]]
