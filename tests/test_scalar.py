from bloqade import cast, var
import bloqade.ir.scalar as scalar
import pytest
from decimal import Decimal
from io import StringIO
from IPython.lib.pretty import PrettyPrinter as PP


def test_var():
    assert var("a") == scalar.Variable("a")
    assert var("a") != scalar.Variable("b")

    with pytest.raises(TypeError):
        var(1)

    with pytest.raises(ValueError):
        var("a*b")

    Vv = var("a")
    vs = var(Vv)

    assert vs == Vv

    mystdout = StringIO()
    p = PP(mystdout)
    Vv._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "Variable: a\n"


def test_cast():
    assert cast("a") == scalar.Variable("a")
    assert cast(1) == scalar.Literal(Decimal("1"))
    assert cast(1.20391023) == scalar.Literal(Decimal("1.20391023"))

    with pytest.raises(ValueError):
        cast("a-b")

    mystdout = StringIO()
    p = PP(mystdout)
    cast(1)._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "Literal: 1\n"


def test_add():
    assert var("a") + var("b") == scalar.Add(var("a"), var("b"))
    assert var("a") + 1 == scalar.Add(var("a"), scalar.Literal(Decimal("1")))
    assert 0 + var("a") == var("a")
    assert var("a") + 0 == var("a")
    assert 1 + var("a") == scalar.Add(scalar.Literal(Decimal("1")), var("a"))
    assert cast(1) + cast(2) == scalar.Literal(Decimal("3"))

    mystdout = StringIO()
    p = PP(mystdout)
    (1 + var("a"))._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "+\n├─ Literal: 1\n⋮\n└─ Variable: a⋮\n"


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

    mystdout = StringIO()
    p = PP(mystdout)
    (3 * var("a"))._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "*\n├─ Literal: 3\n⋮\n└─ Variable: a⋮\n"


def test_div():
    assert var("a") / var("b") == scalar.Div(var("a"), var("b"))
    assert 1 / var("a") == scalar.Div(cast(1), var("a"))
    assert var("a") / 1 == var("a")
    assert 3 / var("a") == scalar.Div(cast(3), var("a"))
    assert cast(1) / cast(2) == cast(0.5)

    mystdout = StringIO()
    p = PP(mystdout)
    (3 / var("a"))._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "/\n├─ Literal: 3\n⋮\n└─ Variable: a⋮\n"


@pytest.mark.skip(reason="no longer supported")
def test_list_of_var():
    pylist = ["a", "b", "c"]
    vlist = var(pylist)
    for pyobj, bobj in zip(pylist, vlist):
        assert bobj == var(pyobj)


@pytest.mark.skip(reason="no longer supported")
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
    with pytest.raises(TypeError):
        var(va)


def test_invalid_keyword():
    with pytest.raises(ValueError):
        var("config_file")

    with pytest.raises(ValueError):
        var("clock_s")


def test_negative_node():
    sa = cast(1.0)
    nsa = scalar.Negative(sa)

    assert nsa.children() == [sa]
    assert nsa.print_node() == "Negative"

    assert str(nsa) == "-(1.0)"


# def test_base_invalid():


def test_interval():
    itvl = scalar.Interval(start=cast(0.0), stop=cast(1.0))
    itvl_no_start = scalar.Interval(None, stop=cast(1.0))
    itvl_no_stop = scalar.Interval(start=cast(0), stop=None)
    itvl_wrong = scalar.Interval(None, None)

    assert itvl.print_node() == "Interval"

    with pytest.raises(ValueError):
        str(itvl_wrong)

    assert str(itvl) == "0.0:1.0"
    assert str(itvl_no_start) == ":1.0"
    assert str(itvl_no_stop) == "0:"

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


def test_add_scalar():
    A = cast(1)
    B = cast(2)

    C = scalar.Add(A, B)

    assert C.children() == [A, B]
    assert C.print_node() == "+"
    assert str(C) == "(1 + 2)"


def test_add_zero():
    A = cast(1)
    B = cast(2)

    C = scalar.Add(A, B)  # expression
    zero = cast(0.0)

    LC = scalar.Scalar.canonicalize(scalar.Add(C, zero))
    RC = scalar.Scalar.canonicalize(scalar.Add(zero, C))

    assert LC == cast(3)
    assert RC == cast(3)


def test_mul_one():
    A = cast(2)
    B = cast(2)

    C = scalar.Add(A, B)  # expression
    one = cast(1.0)

    LC = scalar.Scalar.canonicalize(scalar.Mul(C, one))
    RC = scalar.Scalar.canonicalize(scalar.Mul(one, C))

    assert LC == cast(4)
    assert RC == cast(4)


def test_div_rone():
    A = cast(2)
    B = cast(2)

    C = scalar.Add(A, B)  # expression
    one = cast(1.0)

    LC = scalar.Scalar.canonicalize(scalar.Div(C, one))

    assert LC == cast(4)

    dC = A / B
    assert dC == cast(1)


def test_mul_scalar():
    A = cast(1)
    B = cast(2)

    C = scalar.Mul(A, B)

    assert C.children() == [A, B]
    assert C.print_node() == "*"
    assert str(C) == "(1 * 2)"


def test_div_scalar():
    A = cast(1)
    B = cast(2)

    C = scalar.Div(A, B)

    assert C.children() == [A, B]
    assert C.print_node() == "/"
    assert str(C) == "(1 / 2)"

    assert C() == 0.5


def test_min_scalar():
    A = cast(1)
    B = cast(2)
    C = cast(3)

    D = scalar.Min([A, B, C])
    assert D.children() == [A, B, C]
    assert D.print_node() == "min"
    assert str(D) == "scalar.Min(frozenset({1, 2, 3}))"

    mystdout = StringIO()
    p = PP(mystdout)
    D._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "min\n├─ Literal: 1\n⋮\n├─ Literal: 2\n⋮\n└─ Literal: 3⋮\n"
    )


def test_max_scalar():
    A = cast(1)
    B = cast(2)
    C = cast(3)

    D = scalar.Max([A, B, C])
    assert D.children() == [A, B, C]
    assert D.print_node() == "max"
    assert str(D) == "scalar.Max(frozenset({1, 2, 3}))"

    mystdout = StringIO()
    p = PP(mystdout)
    D._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "max\n├─ Literal: 1\n⋮\n├─ Literal: 2\n⋮\n└─ Literal: 3⋮\n"
    )


def test_cast_decimal():
    A = cast(Decimal("1.0"))

    assert A.value == Decimal("1.0")


def test_Interval_from_pyslice():
    with pytest.raises(ValueError):
        scalar.Interval.from_slice(slice(None, None, None))

    with pytest.raises(ValueError):
        scalar.Interval.from_slice(slice(None, 3, 3))

    with pytest.raises(ValueError):
        scalar.Interval.from_slice(slice(3, None, 3))

    with pytest.raises(ValueError):
        scalar.Interval.from_slice(slice(3, 3, 3))

    with pytest.raises(ValueError):
        scalar.Interval.from_slice(slice(None, None, 3))

    itvl = scalar.Interval.from_slice(slice(5, 6, None))
    assert itvl.start == cast(5)
    assert itvl.stop == cast(6)


def test_Slice():
    itvl = scalar.Interval(cast(5), cast(6))

    slc = scalar.Slice(cast(1), itvl)

    assert str(slc) == "1[5:6]"
    assert slc.children() == {"Scalar": cast(1), None: itvl}
    assert slc.print_node() == "Slice"

    mystdout = StringIO()
    p = PP(mystdout)

    slc._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "Slice\n"
        + "├─ Scalar\n"
        + "│  ⇒ Literal: 1\n"
        + "⋮\n"
        + "└─ Interval\n"
        + "⋮\n"
    )


def test_default_variable_methods():
    default_var = scalar.DefaultVariable("a", cast(1.0))

    assert default_var.children() == [cast(1.0)]
    assert default_var.print_node() == "DefaultVariable: a"
    assert str(default_var) == "a"


@pytest.mark.skip(reason="Changed implementation of static_assign")
def test_static_assign():
    literal = cast(1.0)
    assert literal == literal.static_assign(a=1, b=2)

    float_value = 1.394023

    variable = var("A")
    assert variable == variable.static_assign(b=2)
    assert cast(float_value) == variable.static_assign(A=float_value)

    default_var = scalar.DefaultVariable("A", Decimal("1.0"))
    assert default_var == default_var.static_assign(b=2)
    assert cast(float_value) == default_var.static_assign(A=float_value)

    expr = var("a") + var("b")
    assert cast(float_value) + var("b") == expr.static_assign(a=float_value)
    assert var("a") + cast(float_value) == expr.static_assign(b=float_value)

    expr = var("a") * var("b")
    assert cast(float_value) * var("b") == expr.static_assign(a=float_value)
    assert var("a") * cast(float_value) == expr.static_assign(b=float_value)

    expr = var("a") / var("b")
    assert cast(float_value) / var("b") == expr.static_assign(a=float_value)
    assert var("a") / cast(float_value) == expr.static_assign(b=float_value)

    expr = -var("a")
    assert expr == expr.static_assign(b=float_value)
    assert -cast(float_value) == expr.static_assign(a=float_value)

    a = var("a")
    b = var("b")
    c = var("c")
    expr = scalar.Slice(a, scalar.Interval(b, c))
    assert scalar.Slice(cast(float_value), scalar.Interval(b, c)) == expr.static_assign(
        a=float_value
    )
    assert scalar.Slice(a, scalar.Interval(cast(float_value), c)) == expr.static_assign(
        b=float_value
    )
    assert scalar.Slice(a, scalar.Interval(b, cast(float_value))) == expr.static_assign(
        c=float_value
    )
    assert scalar.Slice(
        cast(float_value), scalar.Interval(cast(float_value), c)
    ) == expr.static_assign(a=float_value, b=float_value)
    assert scalar.Slice(
        cast(float_value), scalar.Interval(b, cast(float_value))
    ) == expr.static_assign(a=float_value, c=float_value)
    assert scalar.Slice(
        a, scalar.Interval(cast(float_value), cast(float_value))
    ) == expr.static_assign(b=float_value, c=float_value)
    assert scalar.Slice(
        cast(float_value), scalar.Interval(cast(float_value), cast(float_value))
    ) == expr.static_assign(a=float_value, b=float_value, c=float_value)

    expr = scalar.Min(set(map(cast, ["a", "b", "c"])))
    assert scalar.Min(set(map(cast, [float_value, "b", "c"]))) == expr.static_assign(
        a=float_value
    )

    expr = scalar.Max(set(map(cast, ["a", "b", "c"])))
    assert scalar.Max(set(map(cast, [float_value, "b", "c"]))) == expr.static_assign(
        a=float_value
    )
