from pydantic.dataclasses import dataclass
from typing import List, Tuple, Generator, Optional
import numpy as np
import itertools
from numpy.typing import NDArray
from .base import AtomArrangement
from bokeh.models import ColumnDataSource, Plot
from bokeh.plotting import figure


class Cell:
    def __init__(self, natoms: int, ndims: int) -> None:
        self.natoms = natoms
        self.ndims = ndims


@dataclass
class BoundedBravais(AtomArrangement):
    shape: Tuple[int, ...]
    lattice_spacing: float

    def __init__(self, *shape: int, lattice_spacing=1.0):
        super().__init__()
        self.shape = shape
        self.lattice_spacing = lattice_spacing
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

    def enumerate(self) -> Generator[NDArray, None, None]:
        for index in itertools.product(*[range(n) for n in self.shape]):
            for pos in self.coordinates(index):
                yield self.lattice_spacing * pos

    def figure(self) -> Plot:
        xs, ys, labels = [], [], []
        for idx, (x, y) in enumerate(self.enumerate()):
            xs.append(x)
            ys.append(y)
            labels.append(idx)

        source = ColumnDataSource(data=dict(x=xs, y=ys, labels=labels))
        p = figure(
            width=400,
            height=400,
            tools="hover,wheel_zoom,box_zoom,reset",
        )
        p.circle("x", "y", source=source, radius=0.08)
        return p


@dataclass
class Chain(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: float = 1.0):
        super().__init__(L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0]]


@dataclass
class Square(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: float = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, 1]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]


@dataclass
class Rectangular(BoundedBravais):
    ratio: float = 1.0

    def __init__(
        self,
        width: int,
        height: int,
        lattice_sapcing_x: float = 1.0,
        lattice_spacing_y: Optional[float] = None,
    ):
        super().__init__(width, height, lattice_spacing=lattice_sapcing_x)
        if lattice_spacing_y:
            self.ratio = lattice_spacing_y / lattice_sapcing_x
        else:
            self.ratio = 1.0

    def cell_vectors(self) -> List[List[float]]:
        return [[1, 0], [0, self.ratio]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0, 0]]


@dataclass
class Honeycomb(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: float = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, np.sqrt(3) / 2]]


@dataclass
class Triangular(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: float = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0]]


@dataclass
class Lieb(BoundedBravais):
    """Lieb lattice."""

    def __init__(self, L: int, lattice_spacing: float = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [0.0, 1.0]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 2, 0.0], [0.0, 1 / 2]]


@dataclass
class Kagome(BoundedBravais):
    def __init__(self, L: int, lattice_spacing: float = 1.0):
        super().__init__(L, L, lattice_spacing=lattice_spacing)

    def cell_vectors(self) -> List[List[float]]:
        return [[1.0, 0.0], [1 / 2, np.sqrt(3) / 2]]

    def cell_atoms(self) -> List[List[float]]:
        return [[0.0, 0.0], [1 / 4, np.sqrt(3) / 4], [3 / 4, np.sqrt(3) / 2]]
