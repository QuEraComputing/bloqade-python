from dataclasses import dataclass
from scipy.sparse import csr_matrix, csc_matrix
import numpy as np
from numpy.typing import NDArray
from beartype.typing import Any, Union
from beartype.vale import IsAttr, IsEqual
from beartype import beartype
from typing import Annotated
from numba import njit


@njit(cache=True)
def _csc_matvec_impl(ncol, data, indices, indptr, scale, input, output):
    for i in range(ncol):
        for j in range(indptr[i], indptr[i + 1]):
            output[indices[j]] += scale * data[j] * input[i]

    return output

@njit(cache=True)
def _csr_matvec_impl(nrow, data, indices, indptr, scale, input, output):
    for i in range(nrow):
        row_out = output[i]
        row_out = 0.0
        for j in range(indptr[i], indptr[i + 1]):
            row_out += data[j] * input[indices[j]]

        output[i] = scale * row_out

    return output


@dataclass(frozen=True)
class SparseMatrixCSC:
    data: NDArray
    indices: NDArray
    indptr: NDArray
    shape: tuple[int, int]

    @staticmethod
    def create(arg1, shape=None, dtype=None, copy=False) -> "SparseMatrixCSC":
        mat = csc_matrix(arg1, shape=shape, dtype=dtype, copy=copy)
        return SparseMatrixCSC(mat.data, mat.indices, mat.indptr, mat.shape)

    def tocsr(self):
        return csc_matrix((self.data, self.indices, self.indptr), self.shape).tocsr()

    @property
    def T(self):
        return SparseMatrixCSR(self.data, self.indices, self.indptr, self.shape[::-1])

    def matvec(self, other, out=None, scale=1):
        if out is None:
            out = np.zeros_like(other, dtype=np.result_type(scale, self.data, other))

        return _csc_matvec_impl(
            self.shape[1], self.data, self.indices, self.indptr, scale, other, out
        )


@dataclass(frozen=True)
class SparseMatrixCSR:
    data: NDArray
    indices: NDArray
    indptr: NDArray
    shape: tuple[int, int]

    @staticmethod
    def create(arg1, shape=None, dtype=None, copy=False) -> "SparseMatrixCSR":
        mat = csr_matrix(arg1, shape=shape, dtype=dtype, copy=copy)
        return SparseMatrixCSR(mat.data, mat.indices, mat.indptr, mat.shape)

    def tocsr(self):
        return csr_matrix((self.data, self.indices, self.indptr), self.shape)

    def toarray(self):
        return csr_matrix((self.data, self.indices, self.indptr), self.shape).toarray()

    @property
    def T(self):
        return SparseMatrixCSC(self.data, self.indices, self.indptr, self.shape[::-1])

    def matvec(self, other, out=None, scale=1):
        if out is None:
            out = np.zeros_like(other, dtype=np.result_type(scale, self.data, other))

        return _csr_matvec_impl(
            self.shape[0], self.data, self.indices, self.indptr, scale, other, out
        )


@njit(cache=True)
def _index_mapping_slice_row(nrow, col_indices, scale, input, output):
    for i in range(nrow):
        output[i] += scale * input[col_indices[i]]

    return output

@njit(cache=True)
def _index_mapping_slice_col(nrow, row_indices, scale, input, output):
    for i in range(nrow):
        output[row_indices[i]] += scale * input[i]

    return output

@njit(cache=True)
def _index_mapping_impl(nrow, col_indices, row_indices, scale, input, output):

    for i in range(row_indices.size):
        output[row_indices[i]] += scale * input[col_indices[i]]

    return output

# use csr_matrix/csc_matrix for rabi-terms that span multiple sites.
# use IndexMapping for local rabi-terms
@dataclass(frozen=True)
class IndexMapping:
    n_row: int
    row_indices: Union[slice, NDArray]
    col_indices: Union[slice, NDArray]

    @property
    def T(self) -> "IndexMapping":
        return IndexMapping(self.n_row, self.col_indices, self.row_indices)

    def matvec(self, other, out=None, scale=1):
        if out is None:
            out = np.zeros_like(other, dtype=np.result_type(scale, other))

        if isinstance(self.col_indices,slice):
            return _index_mapping_slice_row(
                self.n_row, self.row_indices, scale, other, out
            )
        elif isinstance(self.row_indices,slice):
            return _index_mapping_slice_col(
                self.n_row, self.col_indices, scale, other, out
            )
        elif isinstance(self.row_indices, slice) and isinstance(self.col_indices, slice):
            out += scale * other
            return out
        else:
            return _index_mapping_impl(
                self.n_row, self.col_indices, self.row_indices, scale, other, out
            )


    def tocsr(self):
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

        return SparseMatrixCSR.create(
            (data, indices, indptr), shape=(self.n_row, self.n_row)
        )

    def tocsc(self):
        return self.T.tocsr().T
