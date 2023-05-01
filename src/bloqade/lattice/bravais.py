from pydantic.dataclasses import dataclass
from typing import List, TypeVar, Generator
import numpy as np
import itertools
from numpy.typing import NDArray
from .base import Lattice


class Cell:
    def __init__(self, natoms: int, ndims: int) -> None:
        self.natoms = natoms
        self.ndims = ndims


@dataclass(frozen=True)
class BoundedBravais(Lattice):
    shape: List[int]

    def cell_vectors(self) -> List[List[float]]:
        raise NotImplementedError

    def cell_atoms(self) -> List[List[float]]:
        raise NotImplementedError

    def cell(self) -> Cell:
        return Cell(natoms=len(self.cell_atoms()), ndims=len(self.cell_vectors()))

    def coordinates(self, index: List[int]) -> NDArray:
        """calculate the coordinates of a cell in the lattice
        given the cell index.
        """
        # damn! this is like stone age broadcasting
        vectors = np.array(self.cell_vectors())
        index = np.array(index)
        pos = np.sum(index * vectors.T, axis=1)
        return pos + np.array(self.cell_atoms())

    def enumerate(self) -> Generator[NDArray, None, None]:
        for index in itertools.product(*[range(n) for n in self.shape]):
            for pos in self.coordinates(index):
                yield pos


@dataclass(frozen=True)
class Chain(BoundedBravais):
    def cell_vectors(self) -> List[List[float]]:
        return [[1]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0]]


@dataclass(frozen=True)
class Square(BoundedBravais):
    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, 1]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]


@dataclass(frozen=True)
class Rectangular(BoundedBravais):
    ratio: float

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, self.ratio]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]


@dataclass(frozen=True)
class Honeycomb(BoundedBravais):
    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, np.sqrt(3) / 2]]


@dataclass(frozen=True)
class Triangular(BoundedBravais):
    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0]]


@dataclass(frozen=True)
class Lieb(BoundedBravais):
    """Lieb lattice."""

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [0.0, 1.0]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, 0.0], [0.0, 1 / 2]]


@dataclass(frozen=True)
class Kagome(BoundedBravais):
    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 4, np.sqrt(3) / 4], [3 / 4, np.sqrt(3) / 2]]
