from bloqade.ir import scalar

# from bloqade.ir.control import waveform, field, pulse, sequence
from bloqade import var, cast

from decimal import Decimal


class TestScalar:
    def test_add(self):
        assert var("a") + var("b") == scalar.Add(var("a"), var("b"))
        assert var("a") + 1 == scalar.Add(var("a"), scalar.Literal(Decimal("1")))
        assert 0 + var("a") == var("a")
        assert var("a") + 0 == var("a")
        assert 1 + var("a") == scalar.Add(scalar.Literal(Decimal("1")), var("a"))
        assert cast(1) + cast(2) == scalar.Literal(Decimal("3"))
        assert -cast("a") + -cast("b") == scalar.Negative(
            expr=scalar.Add(var("a"), var("b"))
        )

    def test_sub(self):
        assert var("a") - var("b") == scalar.Add(var("a"), scalar.Negative(var("b")))
        assert var("a") - 1 == scalar.Add(var("a"), cast(-1))
        assert 1 - var("a") == scalar.Add(
            scalar.Literal(Decimal("1")), scalar.Negative(var("a"))
        )
        assert cast(1) - cast(2) == scalar.Literal(Decimal("-1"))
        assert -cast(1) + cast(2) == scalar.Literal(Decimal("1"))

    def test_mul(self):
        assert var("a") * var("b") == scalar.Mul(var("a"), var("b"))
        assert 1 * var("a") == var("a")
        assert var("a") * 1 == var("a")
        assert 3 * var("a") == scalar.Mul(scalar.Literal(Decimal("3")), var("a"))
        assert cast(1) * cast(2) == scalar.Literal(Decimal("2"))
        assert -cast("a") * -cast("b") == cast("a") * cast("b")
        assert -cast("a") * cast("b") == -(cast("a") * cast("b"))
        assert cast("a") * -cast("b") == -(cast("a") * cast("b"))

    def test_div(self):
        assert var("a") / var("b") == scalar.Div(var("a"), var("b"))
        assert 1 / var("a") == scalar.Div(cast(1), var("a"))
        assert var("a") / 1 == var("a")
        assert 3 / var("a") == scalar.Div(cast(3), var("a"))
        assert cast(1) / cast(2) == cast(0.5)
        assert cast(0) / cast("a") == cast(0)
        assert -cast("a") / -cast("b") == cast("a") / cast("b")
        assert -cast("a") / cast("b") == -(cast("a") / cast("b"))
        assert cast("a") / -cast("b") == -(cast("a") / cast("b"))

    def test_negative_node(self):
        sa = cast(1.0)
        nsa = -sa

        assert -sa == cast(-1.0)
        assert -nsa == sa
