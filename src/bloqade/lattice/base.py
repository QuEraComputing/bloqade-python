from ..builder import RydbergBuilder, HyperfineBuilder, BuildStart
from numpy.typing import NDArray
from typing import List, Generator
import numpy as np
import matplotlib.pyplot as plt


class Lattice(BuildStart):
    def enumerate(self) -> Generator[NDArray, None, None]:
        """enumerate all positions in the lattice."""
        raise NotImplementedError

    def figure(self) -> plt.Figure:
        """plot the lattice."""
        raise NotImplementedError

    def plot(self, ax: plt.Axes) -> plt.Axes:
        """plot the lattice on the given axes."""
        raise NotImplementedError

    def show(self) -> None:
        """show the lattice."""
        self.figure().show()

    @property
    def n_atoms(self):
        raise NotImplementedError

    @property
    def n_dims(self):
        raise NotImplementedError
