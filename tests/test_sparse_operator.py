from bloqade.emulate.sparse_operator import (
    SparseMatrixCSC,
    SparseMatrixCSR,
    IndexMapping,
    _csc_matvec_impl,
    _csr_matvec_impl,
    _index_mapping_col_sliced,
    _index_mapping_row_sliced,
    _index_mapping_impl,
    _index_mapping_row_col_sliced,
)
from scipy.sparse import random
import numpy as np

np.random.seed(12039)


def test_csr():
    A = random(10, 10, density=0.5, format="csr")
    B = SparseMatrixCSR.create(A)
    assert np.allclose(A.toarray(), B.toarray())

    v = np.random.normal(size=10)
    a = 3

    expected_result = a * A.dot(v) + v
    result = v.copy()
    B.matvec(v, out=result, scale=a)

    assert np.allclose(result, expected_result)

    result = v.copy()

    _csr_matvec_impl.py_func(B.shape[1], B.data, B.indices, B.indptr, a, v, result)

    assert np.allclose(result, expected_result)


def test_csc():
    A = random(10, 10, density=0.5, format="csc")
    B = SparseMatrixCSC.create(A)
    assert np.allclose(A.toarray(), B.toarray())

    v = np.random.normal(size=10)
    a = 3

    expected_result = a * A.dot(v) + v
    result = v.copy()
    B.matvec(v, out=result, scale=a)

    assert np.allclose(result, expected_result)

    result = v.copy()

    _csc_matvec_impl.py_func(B.shape[1], B.data, B.indices, B.indptr, a, v, result)

    assert np.allclose(result, expected_result)


def test_index_mapping():
    B = IndexMapping(10, slice(0, None, 2), slice(1, None, 2))
    A = B.tocsr().toarray()

    v = np.random.normal(size=10)
    a = 3

    expected_result = a * A.dot(v) + v

    result = v.copy()
    B.matvec(v, out=result, scale=a)

    print(result)
    print(expected_result)
    print("---------------")

    assert np.allclose(result, expected_result)

    result = v.copy()

    _index_mapping_row_col_sliced.py_func(
        a,
        v[B.col_indices],
        result[B.row_indices],
    )

    print(result)
    print(expected_result)

    assert np.allclose(result, expected_result)


def test_index_mapping_2():
    input = np.random.permutation(np.arange(10))

    B = IndexMapping(10, input, slice(None))
    A = B.tocsr().toarray()

    v = np.random.normal(size=10)
    a = 3
    print(A)

    expected_result = a * A.dot(v) + v

    result = v.copy()
    B.matvec(v, out=result, scale=a)

    print(result)
    print(expected_result)
    print("---------------")

    assert np.allclose(result, expected_result)

    result = v.copy()

    _index_mapping_col_sliced.py_func(
        B.row_indices,
        a,
        v[B.col_indices],
        result,
    )

    print(result)
    print(expected_result)

    assert np.allclose(result, expected_result)

    B = B.T
    A = B.tocsr().toarray()

    expected_result = a * A.dot(v) + v

    result = v.copy()
    B.matvec(v, out=result, scale=a)

    print(result)
    print(expected_result)
    print("---------------")

    assert np.allclose(result, expected_result)

    result = v.copy()

    _index_mapping_row_sliced.py_func(
        B.col_indices,
        a,
        v,
        result[B.row_indices],
    )

    print(result)
    print(expected_result)

    assert np.allclose(result, expected_result)


def test_index_mapping_3():
    input = np.random.permutation(np.arange(10))
    output = np.random.permutation(np.arange(10))

    B = IndexMapping(10, input, output)
    A = B.tocsr().toarray()

    v = np.random.normal(size=10)
    a = 3

    expected_result = a * A.dot(v) + v

    result = v.copy()
    B.matvec(v, out=result, scale=a)

    print(result)
    print(expected_result)
    print("---------------")

    assert np.allclose(result, expected_result)

    result = v.copy()

    _index_mapping_impl.py_func(
        B.col_indices,
        B.row_indices,
        a,
        v,
        result,
    )

    print(result)
    print(expected_result)

    assert np.allclose(result, expected_result)
