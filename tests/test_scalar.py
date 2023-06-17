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
