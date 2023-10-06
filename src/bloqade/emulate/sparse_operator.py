from dataclasses import dataclass
from functools import cached_property
from scipy.sparse import csr_matrix, csc_matrix, coo_matrix
import numpy as np
from numpy.typing import NDArray
from beartype.typing import Union
from numba import njit

# from beartype.vale import IsAttr, IsEqual
# from beartype import beartype
# from typing import Annotated


@njit(cache=True)
def _csc_matvec_impl(ncol, data, indices, indptr, scale, input, output):
    for i in range(ncol):
        for j in range(indptr[i], indptr[i + 1]):
            output[indices[j]] += scale * data[j] * input[i]

    return output


@njit(cache=True)
def _csr_matvec_impl(nrow, data, indices, indptr, scale, input, output):
    for i in range(nrow):
        row_out = np.zeros_like(output[i])
        for j in range(indptr[i], indptr[i + 1]):
            row_out += data[j] * input[indices[j]]

        output[i] += scale * row_out

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

    def toarray(self):
        return self.tocsr().toarray()

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
        return self.tocsr().toarray()

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
def _index_mapping_row_col_sliced(scale, input, output):
    for i in range(output.size):
        output[i] += scale * input[i]

    return output


@njit(cache=True)
def _index_mapping_row_sliced(col_indices, scale, input, output):
    for i in range(col_indices.size):
        output[i] += scale * input[col_indices[i]]

    return output


@njit(cache=True)
def _index_mapping_col_sliced(row_indices, scale, input, output):
    for i in range(row_indices.size):
        output[row_indices[i]] += scale * input[i]

    return output


@njit(cache=True)
def _index_mapping_impl(col_indices, row_indices, scale, input, output):
    for i in range(row_indices.size):
        output[row_indices[i]] += scale * input[col_indices[i]]

    return output


# use csr_matrix/csc_matrix for rabi-terms that span multiple sites.
# use IndexMapping for local rabi-terms
@dataclass(frozen=True)
class IndexMapping:
    n_row: int
    row_indices: Union[NDArray, slice]
    col_indices: Union[NDArray, slice]

    @property
    def T(self) -> "IndexMapping":
        return IndexMapping(self.n_row, self.col_indices, self.row_indices)

    @cached_property
    def _matvec_dispatcher(self):
        if isinstance(self.col_indices, slice) and isinstance(self.row_indices, slice):

            def _matvec_imp(col_indices, row_indices, scale, input, output):
                return _index_mapping_row_col_sliced(
                    scale, input[col_indices], output[row_indices]
                )

        elif isinstance(self.col_indices, slice):
            print(self.col_indices, self.row_indices)

            def _matvec_imp(col_indices, row_indices, scale, input, output):
                return _index_mapping_col_sliced(
                    row_indices, scale, input[col_indices], output
                )

        elif isinstance(self.row_indices, slice):

            def _matvec_imp(col_indices, row_indices, scale, input, output):
                return _index_mapping_row_sliced(
                    col_indices, scale, input, output[row_indices]
                )

        else:

            def _matvec_imp(col_indices, row_indices, scale, input, output):
                return _index_mapping_impl(
                    col_indices, row_indices, scale, input, output
                )

        return _matvec_imp

    def matvec(self, other, out=None, scale=1):
        if out is None:
            out = np.zeros_like(other, dtype=np.result_type(scale, other))

        return self._matvec_dispatcher(
            self.col_indices, self.row_indices, scale, other, out
        )

    def tocoo(self) -> coo_matrix:
        if isinstance(self.row_indices, slice):
            row_slice = self.row_indices
            start = row_slice.start if row_slice.start is not None else 0
            stop = row_slice.stop if row_slice.stop is not None else self.n_row
            step = row_slice.step if row_slice.step is not None else 1
            rows = np.arange(start, stop, step)
        elif (
            isinstance(self.row_indices, np.ndarray) and self.row_indices.dtype == bool
        ):
            rows = np.where(self.row_indices)[0]
        else:
            rows = self.row_indices

        if isinstance(self.col_indices, slice):
            col_slice = self.col_indices
            start = col_slice.start if col_slice.start is not None else 0
            stop = col_slice.stop if col_slice.stop is not None else self.n_row
            step = col_slice.step if col_slice.step is not None else 1

            cols = np.arange(start, stop, step)
        elif (
            isinstance(self.col_indices, np.ndarray) and self.col_indices.dtype == bool
        ):
            cols = np.where(self.col_indices)[0]
        else:
            cols = self.col_indices

        data = np.ones(rows.size)

        return coo_matrix((data, (rows, cols)), shape=(self.n_row, self.n_row))

    def tocsc(self):
        return self.tocoo().tocsc()

    def tocsr(self):
        return self.tocoo().tocsr()
