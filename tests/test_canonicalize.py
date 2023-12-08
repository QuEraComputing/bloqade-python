import bloqade.rewrite.common.canonicalize as canonicalize

from bloqade.ir import scalar
from bloqade.ir.control import waveform
from bloqade import var, cast
from decimal import Decimal


class TestUtils:
    def test_is_literal(self):
        assert canonicalize.is_literal(cast(1))
        assert not canonicalize.is_literal(var("a"))

    def test_is_negative(self):
        assert canonicalize.is_negative(-var("a"))
        assert not canonicalize.is_negative(var("a"))
        # canonicalize will put negative node into literals
        assert not canonicalize.is_negative(-cast(1))

    def test_is_zero(self):
        assert canonicalize.is_zero(cast(0))
        assert not canonicalize.is_zero(cast(1))
        assert not canonicalize.is_zero(var("a"))

    def test_is_one(self):
        assert canonicalize.is_one(cast(1))
        assert not canonicalize.is_one(cast(0))
        assert not canonicalize.is_one(var("a"))

    def test_is_scaled_waveform(self):
        assert canonicalize.is_scaled_waveform(cast("a") * waveform.Linear(0, 1, 1))

    def test_is_constant_waveform(self):
        assert canonicalize.is_constant_waveform(waveform.Constant(1, 1))


class TestScalar:
    def test_add(self):
        assert var("a") + var("b") == scalar.Add(var("a"), var("b"))
        assert var("a") + 1 == scalar.Add(var("a"), scalar.Literal(Decimal("1")))
        assert 0 + var("a") == var("a")
        assert var("a") + 0 == var("a")
        assert 1 + var("a") == scalar.Add(scalar.Literal(Decimal("1")), var("a"))
        assert cast(1) + cast(2) == scalar.Literal(Decimal("3"))
        assert var("a") - var("b") == scalar.Add(var("a"), scalar.Negative(var("b")))
        assert var("a") - 1 == scalar.Add(var("a"), cast(-1))
        assert cast(1) - cast(2) == scalar.Literal(Decimal("-1"))
        assert -cast(1) + cast(2) == scalar.Literal(Decimal("1"))
        assert 1 - var("a") == scalar.Add(
            scalar.Literal(Decimal("1")), scalar.Negative(var("a"))
        )
        assert -cast("a") + -cast("b") == scalar.Negative(
            expr=scalar.Add(var("a"), var("b"))
        )
        assert var("a") - var("a") == cast(0)
        assert -var("a") + var("a") == cast(0)

    def test_mul(self):
        assert var("a") * var("b") == scalar.Mul(var("a"), var("b"))
        assert 1 * var("a") == var("a")
        assert var("a") * 1 == var("a")
        assert 3 * var("a") == scalar.Mul(scalar.Literal(Decimal("3")), var("a"))
        assert cast(1) * cast(2) == scalar.Literal(Decimal("2"))
        assert -cast("a") * -cast("b") == cast("a") * cast("b")
        assert -cast("a") * cast("b") == -(cast("a") * cast("b"))
        assert cast("a") * -cast("b") == -(cast("a") * cast("b"))
        assert cast(0) * cast("a") == cast(0)
        assert cast(2) * cast(2) == cast(4)

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
        assert -cast(1.0) == cast(-1.0)
        assert -(-var("a")) == var("a")

    def test_min(self):
        a = var("a")
        b = var("b")
        c = var("c")
        d = cast(1)
        e = cast(2)
        f = cast(3)

        expr1 = a.min(b).min(c)
        expr2 = a.min(d).min(b).min(e).min(c).min(f)

        assert expr1 == scalar.Min([a, b, c])
        assert expr2 == scalar.Min([a, b, c, d])
        assert d.min(e) == d

    def test_max(self):
        a = var("a")
        b = var("b")
        c = var("c")
        d = cast(1)
        e = cast(2)
        f = cast(3)

        expr1 = a.max(b).max(c)
        expr2 = a.max(d).max(b).max(e).max(c).max(f)

        assert expr1 == scalar.Max([a, b, c])
        assert expr2 == scalar.Max([a, b, c, f])
        assert d.max(e) == e


class TestWaveform:
    def test_add(self):
        wf1 = waveform.Linear(0, "a", "T")
        wf2 = waveform.Constant(1, 1)
        wf3 = waveform.Constant(2, 1)
        wf4 = waveform.Poly(["a", "b", "c"], "t")

        assert wf1 + wf1 == 2 * wf1
        assert wf1 + waveform.Constant(1, 0) == wf1
        assert waveform.Constant(1, 0) + wf1 == wf1
        assert wf1 + waveform.Constant(0, 1) == wf1
        assert waveform.Constant(0, 1) + wf1 == wf1
        assert wf2 + wf3 == waveform.Constant(3, 1)
        assert 3.12 * wf1 + 3.12 * wf4 == 3.12 * (wf1 + wf4)
        assert 4.123 * wf1 + 3.13 * wf1 == 7.253 * wf1
        assert 4.123 * wf1 + wf1 == 5.123 * wf1
        assert wf1 + 4.123 * wf1 == 5.123 * wf1

    def test_neg(self):
        wf1 = waveform.Linear(0, "a", "T")
        wf2 = waveform.Constant(1, 1)

        assert -(-wf1) == wf1
        assert -wf2 == waveform.Constant(-1, 1)
        assert -(-var("a") * wf1) == var("a") * wf1

    def test_scale(self):
        wf1 = waveform.Linear(0, "a", "T")
        wf2 = waveform.Constant(1, 1)

        assert 1 * wf1 == wf1
        assert 0 * wf1 == waveform.Constant(0, "T")
        assert 2 * (3 * wf1) == 6 * wf1
        assert 2 * wf2 == waveform.Constant(2, 1)

    def test_append(self):
        # test nested appends

        wf1 = waveform.Append(
            [
                waveform.Constant(1, 1),
                waveform.Constant(2, 1),
                waveform.Constant(3, 1),
                waveform.Append([waveform.Constant(4, 1), waveform.Constant(5, 1)]),
            ]
        )
        canonicalize.Canonicalizer().visit(wf1) == waveform.Append(
            [
                waveform.Constant(1, 1),
                waveform.Constant(2, 1),
                waveform.Constant(3, 1),
                waveform.Constant(4, 1),
                waveform.Constant(5, 1),
            ]
        )

        wf2 = waveform.Append(
            [
                waveform.Constant(1, 1),
                waveform.Constant(2, 1),
                waveform.Constant(3, 1),
                waveform.Append(
                    [
                        waveform.Constant(4, 1),
                        waveform.Constant(5, 1),
                        waveform.Append(
                            [
                                waveform.Constant(6, 1),
                                waveform.Constant(7, 1),
                            ]
                        ),
                    ]
                ),
            ]
        )
        assert canonicalize.Canonicalizer().visit(wf2) == waveform.Append(
            [
                waveform.Constant(1, 1),
                waveform.Constant(2, 1),
                waveform.Constant(3, 1),
                waveform.Constant(4, 1),
                waveform.Constant(5, 1),
                waveform.Constant(6, 1),
                waveform.Constant(7, 1),
            ]
        )

        wf3 = waveform.Append(
            [
                waveform.Constant(1, 1),
                waveform.Constant(2, 1),
                waveform.Constant(3, 1),
                waveform.Append(
                    [
                        waveform.Constant(3, 1),
                        waveform.Constant(4, 0),
                    ]
                ),
            ]
        )
        # test that the constants are merged
        assert canonicalize.Canonicalizer().visit(wf3) == waveform.Append(
            [
                waveform.Constant(1, 1),
                waveform.Constant(2, 1),
                waveform.Constant(3, 2),
            ]
        )

    def test_slice(self):
        wf1 = waveform.Linear(0, "a", "T")

        T = var("T")

        sliced_wf1 = waveform.Slice(wf1, waveform.Interval(cast(0), T))

        assert canonicalize.Canonicalizer().visit(sliced_wf1) == wf1

        interval = waveform.Interval(var("a"), var("b"))

        assert canonicalize.Canonicalizer().visit(
            waveform.Slice(2.123 * wf1, interval)
        ) == 2.123 * waveform.Slice(wf1, interval)

        assert canonicalize.Canonicalizer().visit(
            waveform.Slice(-wf1, interval)
        ) == waveform.Negative(waveform.Slice(wf1, interval))

    def test_negative(self):
        wf1 = waveform.Linear(0, "a", "T")

        assert -(-wf1) == wf1
        assert -waveform.Constant(1, 1) == waveform.Constant(-1, 1)
        assert -waveform.Constant(-1, 1) == waveform.Constant(1, 1)


class TestHigherExpressions:
    def test_field(self):
        pass

    def test_pulse_leaf(self):
        pass

    def test_pulse_slice(self):
        pass

    def test_pulse_append(self):
        pass

    def test_sequence(self):
        pass

    def test_sequence_slice(self):
        pass

    def test_sequence_append(self):
        pass
