from dataclasses import dataclass
from scipy.sparse import csr_matrix
import numpy as np
from numpy.typing import NDArray
from typing import Union


@dataclass(frozen=True)
class Diagonal:  # used to represent detuning + Rydberg
    diagonal: NDArray

    def dot(self, other):
        return self.diagonal * other

    def to_csr(self):
        indices = np.arange(len(self.diagonal))
        indptr = np.arange(len(self.diagonal) + 1)
        data = self.diagonal
        return csr_matrix(
            (data, indices, indptr), shape=(len(self.diagonal), len(self.diagonal))
        )


# use csr_matrix for rabi-terms that span multiple sites.
# use PermMatrix for local rabi-terms
@dataclass(frozen=True)
class IndexMapping:
    n_row: int
    input_indices: Union[slice, NDArray]
    output_indices: Union[slice, NDArray]

    def ajoint(self):
        return IndexMapping(self.output_indices, self.input_indices)

    def dot(self, other, out=None):
        result = np.zeros_like(other)
        result[self.output_indices] = other[self.input_indices]

    def to_csr(self):
        indptr = np.zeros(self.n_row + 1)
        indptr[1:][self.output_indices] = 1
        np.cumsum(indptr, out=indptr)

        if isinstance(self.input_indices, slice):
            indices = np.arange(self.n_row)
        else:
            indices = self.input_indices

        data = np.ones_like(indices)

        return csr_matrix((data, indices, indptr), shape=(self.n_row, self.n_row))
