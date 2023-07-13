from bloqade import cast, var
import bloqade.ir.scalar as scalar
import pytest
from decimal import Decimal


def test_var():
    assert var("a") == scalar.Variable("a")
    assert var("a") != scalar.Variable("b")

    with pytest.raises(TypeError):
        var(1)

    with pytest.raises(ValueError):
        var("a*b")


def test_cast():
    assert cast("a") == scalar.Variable("a")
    assert cast(1) == scalar.Literal(Decimal("1"))
    assert cast(1.20391023) == scalar.Literal(Decimal("1.20391023"))

    with pytest.raises(ValueError):
        cast("a-b")


def test_add():
    assert var("a") + var("b") == scalar.Add(var("a"), var("b"))
    assert var("a") + 1 == scalar.Add(var("a"), scalar.Literal(Decimal("1")))
    assert 0 + var("a") == var("a")
    assert var("a") + 0 == var("a")
    assert 1 + var("a") == scalar.Add(scalar.Literal(Decimal("1")), var("a"))
    assert cast(1) + cast(2) == scalar.Literal(Decimal("3"))


def test_sub():
    assert var("a") - var("b") == scalar.Add(var("a"), scalar.Negative(var("b")))
    assert var("a") - 1 == scalar.Add(var("a"), scalar.Negative(cast(1)))
    assert 1 - var("a") == scalar.Add(
        scalar.Literal(Decimal("1")), scalar.Negative(var("a"))
    )
    assert cast(1) - cast(2) == scalar.Literal(Decimal("-1"))
    assert -cast(1) + cast(2) == scalar.Literal(Decimal("1"))


def test_mul():
    assert var("a") * var("b") == scalar.Mul(var("a"), var("b"))
    assert 1 * var("a") == var("a")
    assert var("a") * 1 == var("a")
    assert 3 * var("a") == scalar.Mul(scalar.Literal(Decimal("3")), var("a"))
    assert cast(1) * cast(2) == scalar.Literal(Decimal("2"))


def test_div():
    assert var("a") / var("b") == scalar.Div(var("a"), var("b"))
    assert 1 / var("a") == scalar.Div(cast(1), var("a"))
    assert var("a") / 1 == var("a")
    assert 3 / var("a") == scalar.Div(cast(3), var("a"))
    assert cast(1) / cast(2) == cast(0.5)


def test_list_of_var():
    pylist = ["a", "b", "c"]
    vlist = var(pylist)
    for pyobj, bobj in zip(pylist, vlist):
        assert bobj == var(pyobj)


def test_tuple_of_var():
    pylist = ("a", "b", "c")
    vlist = var(pylist)
    for pyobj, bobj in zip(pylist, vlist):
        assert bobj == var(pyobj)


def test_var_member():
    va = var("a")

    assert va.children() == []
    assert va.print_node() == "Variable: a"


def test_scalar_var():
    va = cast(1.0)
    vva = var(va)

    assert va == vva

    assert vva.children() == []
    assert vva.print_node() == "Literal: 1.0"


def test_invalid_keyword():
    with pytest.raises(ValueError):
        var("config_file")

    with pytest.raises(ValueError):
        var("clock_s")


def test_negative_node():
    sa = cast(1.0)
    nsa = scalar.Negative(sa)

    assert nsa.children() == [sa]
    assert nsa.print_node() == "-"

    assert nsa.__repr__() == "-(1.0)"


# def test_base_invalid():


def test_interval():
    itvl = scalar.Interval(start=cast(0.0), stop=cast(1.0))
    itvl_no_start = scalar.Interval(None, stop=cast(1.0))
    itvl_no_stop = scalar.Interval(start=cast(0), stop=None)
    itvl_wrong = scalar.Interval(None, None)

    assert itvl.print_node() == "Interval"

    with pytest.raises(ValueError):
        itvl_wrong.__repr__()

    assert itvl.__repr__() == "0.0:1.0"
    assert itvl_no_start.__repr__() == ":1.0"
    assert itvl_no_stop.__repr__() == "0:"

    with pytest.raises(ValueError):
        itvl_wrong.children()

    assert itvl.children() == {"start": cast(0.0), "stop": cast(1.0)}
    assert itvl_no_start.children() == {"stop": cast(1.0)}
    assert itvl_no_stop.children() == {"start": cast(0)}


def test_canonicalize_neg_neg():
    sa = cast(1.0)
    nsa = -sa
    nsa2 = -nsa

    out2 = scalar.Scalar.canonicalize(nsa2)
    assert out2.value == Decimal("1.0")

    sb = cast(-1.0)
    nsb = scalar.Negative(sb)

    out3 = scalar.Scalar.canonicalize(nsb)
    assert out3 == cast(1.0)


def test_canonicalize_add_neg():
    sa = cast(1.0)
    nsa = scalar.Negative(sa)

    outR = scalar.Add(sa, nsa)
    outL = scalar.Add(nsa, sa)

    outR = scalar.Scalar.canonicalize(outR)
    outL = scalar.Scalar.canonicalize(outL)

    assert outR == scalar.Literal(0.0)
    assert outL == scalar.Literal(0.0)

    A = cast(1.0)
    B = cast(2.0)

    C = scalar.Add(A, B)
    nC = -C

    assert scalar.Scalar.canonicalize(scalar.Add(C, nC)) == scalar.Literal(0.0)
    assert scalar.Scalar.canonicalize(scalar.Add(nC, C)) == scalar.Literal(0.0)


def test_canonicalize_mul_zero():
    zero = scalar.Literal(0.0)
    one = cast(1)

    outR = scalar.Mul(zero, one)
    outL = scalar.Mul(one, zero)

    outR = scalar.Scalar.canonicalize(outR)
    outL = scalar.Scalar.canonicalize(outL)

    assert outR == scalar.Literal(0.0)
    assert outL == scalar.Literal(0.0)

    A = cast(1.0)
    B = cast(2.0)

    C = scalar.Add(A, B)

    assert scalar.Scalar.canonicalize(scalar.Mul(zero, C)) == scalar.Literal(0.0)
    assert scalar.Scalar.canonicalize(scalar.Mul(C, zero)) == scalar.Literal(0.0)
