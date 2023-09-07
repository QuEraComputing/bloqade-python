from dataclasses import dataclass
from scipy.sparse import csr_matrix
import numpy as np
from numpy.typing import NDArray
from typing import Union


# use csr_matrix for rabi-terms that span multiple sites.
# use PermMatrix for local rabi-terms
@dataclass(frozen=True)
class IndexMapping:
    n_row: int
    row_indices: Union[slice, NDArray]
    col_indices: Union[slice, NDArray]

    @property
    def T(self) -> "IndexMapping":
        return IndexMapping(self.n_row, self.col_indices, self.row_indices)

    def dot(self, other):
        result = np.zeros_like(other)
        result[self.row_indices] = other[self.col_indices]

    def to_csr(self):
        indptr = np.zeros(self.n_row + 1, dtype=np.int64)
        indptr[1:][self.row_indices] = 1
        np.cumsum(indptr, out=indptr)

        if isinstance(self.col_indices, slice):
            start = self.col_indices.start
            stop = self.col_indices.stop
            step = self.col_indices.step

            if start is None:
                start = 0

            if stop is None:
                stop = self.n_row

            if step is None:
                step = 1

            indices = np.arange(start, stop, step)
        else:
            indices = self.col_indices

        data = np.ones_like(indices)

        return csr_matrix((data, indices, indptr), shape=(self.n_row, self.n_row))
