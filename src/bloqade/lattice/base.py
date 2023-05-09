from ..builder import SequenceStart
from numpy.typing import NDArray
from typing import Generator
from bokeh.plotting import show


class Lattice(SequenceStart):
    def __init__(self) -> None:
        super().__init__()
        self.__lattice__ = self

    def enumerate(self) -> Generator[NDArray, None, None]:
        """enumerate all positions in the lattice."""
        raise NotImplementedError

    def figure(self):
        """plot the lattice."""
        raise NotImplementedError

    def show(self) -> None:
        """show the lattice."""
        show(self.figure())

    @property
    def n_atoms(self):
        raise NotImplementedError

    @property
    def n_dims(self):
        raise NotImplementedError
