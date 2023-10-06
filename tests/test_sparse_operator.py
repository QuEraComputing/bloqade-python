from bloqade.emulate.sparse_operator import (
    SparseMatrixCSC,
    SparseMatrixCSR,
    IndexMapping,
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

    assert np.allclose(result, expected_result)

    B = B.T
    A = B.tocsr().toarray()

    expected_result = a * A.dot(v) + v

    result = v.copy()
    B.matvec(v, out=result, scale=a)

    print(result)
    print(expected_result)

    assert np.allclose(result, expected_result)
