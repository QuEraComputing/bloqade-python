from ..builder import RydbergBuilder, HyperfineBuilder, BuildStart
from numpy.typing import NDArray
from typing import List, Generator
import numpy as np

class Lattice(BuildStart):

    def enumerate(self) -> Generator[NDArray, None, None]:
        """enumerate all positions in the lattice.
        """
        raise NotImplementedError
