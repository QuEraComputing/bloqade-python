from pydantic.dataclasses import dataclass
from typing import List, Tuple, Generator, Optional, Any
import numpy as np
import itertools
from numpy.typing import NDArray
from bloqade.ir.location.base import AtomArrangement, LocationInfo
from bloqade.ir import Scalar, cast


class Cell:
    def __init__(self, natoms: int, ndims: int) -> None:
        self.natoms = natoms
        self.ndims = ndims


@dataclass
class BoundedBravais(AtomArrangement):
    shape: Tuple[int, ...]
    lattice_spacing: Scalar

    def __init__(self, *shape: int, lattice_spacing: Any = 1.0):
        super().__init__()
        self.shape = shape
        self.lattice_spacing = cast(lattice_spacing)
        self.__n_atoms = None
        self.__n_dims = None

    @property
    def n_atoms(self):
        if not self.__n_atoms:
            self.__n_atoms = len(self.cell_atoms()) * np.prod(self.shape)
        return self.__n_atoms

    @property
    def n_dims(self):
        if not self.__n_dims:
            self.__n_dims = len(self.cell_vectors())
        return self.__n_dims

    def coordinates(self, index: List[int]) -> NDArray:
        """calculate the coordinates of a cell in the lattice
        given the cell index.
        """
        # damn! this is like stone age broadcasting
        vectors = np.array(self.cell_vectors())
        index = np.array(index)
        pos = np.sum(index * vectors.T, axis=1)
        return pos + np.array(self.cell_atoms())

    def enumerate(self) -> Generator[LocationInfo, None, None]:
        for index in itertools.product(*[range(n) for n in self.shape]):
            for pos in self.coordinates(index):
                position = tuple(self.lattice_spacing * pos)
                yield LocationInfo(position, True)


@dataclass
class Chain(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: Any = 1.0):
        super().__init__(L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]

    def scale(self, factor: Scalar) -> "Chain":
        return Chain(self.shape[0], lattice_spacing=cast(factor) * self.lattice_spacing)


@dataclass
class Square(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: Any = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, 1]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]

    def scale(self, factor: Scalar) -> "Square":
        return Square(
            self.shape[0], lattice_spacing=cast(factor) * self.lattice_spacing
        )


@dataclass
class Rectangular(BoundedBravais):
    ratio: Scalar = 1.0

    def __init__(
        self,
        width: int,
        height: int,
        lattice_sapcing_x: Any = 1.0,
        lattice_spacing_y: Optional[Any] = None,
    ):
        super().__init__(width, height, lattice_spacing=lattice_sapcing_x)
        if lattice_spacing_y:
            self.ratio = cast(lattice_spacing_y) / cast(lattice_sapcing_x)
        else:
            self.ratio = cast(1.0)

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, self.ratio]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]

    def scale(self, factor: Scalar) -> "Chain":
        lattice_spacing_y = cast(factor) * self.ratio * self.lattice_spacing
        lattice_spacing_x = cast(factor) * self.lattice_spacing
        return Chain(
            self.shape[0],
            lattice_spacing_x=lattice_spacing_x,
            lattice_spacing_y=lattice_spacing_y,
        )


@dataclass
class Honeycomb(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: Any = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def scale(self, factor: Scalar) -> "Honeycomb":
        return Honeycomb(
            self.shape[0], lattice_spacing=cast(factor) * self.lattice_spacing
        )


@dataclass
class Triangular(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: Any = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0]]

    def scale(self, factor: Scalar) -> "Triangular":
        return Triangular(
            self.shape[0], lattice_spacing=cast(factor) * self.lattice_spacing
        )


@dataclass
class Lieb(BoundedBravais):
    """Lieb lattice."""

    def __init__(self, L: int, lattice_spacing: Any = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [0.0, 1.0]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, 0.0], [0.0, 1 / 2]]

    def scale(self, factor: Scalar) -> "Lieb":
        return Lieb(self.shape[0], lattice_spacing=cast(factor) * self.lattice_spacing)


@dataclass
class Kagome(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: Any = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 4, np.sqrt(3) / 4], [3 / 4, np.sqrt(3) / 2]]

    def scale(self, factor: Scalar) -> "Kagome":
        return Kagome(
            self.shape[0], lattice_spacing=cast(factor) * self.lattice_spacing
        )
