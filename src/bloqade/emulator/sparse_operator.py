from pydantic.dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from typing import Union


@dataclass
class Diagonal:  # used to represent detuning + Rydberg
    diagonal: NDArray

    def dot(self, other):
        return self.diagonal * other


# use csr_matrix for rabi-terms that span multiple sites.
# use PermMatrix for local rabi-terms
@dataclass
class IndexMapping:
    input_indices: Union[slice, NDArray]
    output_indices: Union[slice, NDArray] = slice(-1)

    def ajoint(self):
        return IndexMapping(self.output_indices, self.input_indices)

    def dot(self, other, out=None):
        result = np.zeros_like(other)
        result[self.output_indices] = other[self.input_indices]
