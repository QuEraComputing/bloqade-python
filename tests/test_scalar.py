from pydantic import ValidationError
from bloqade import cast, var
import bloqade.ir.scalar as scalar
import pytest
from decimal import Decimal
from io import StringIO
from IPython.lib.pretty import PrettyPrinter as PP
import bloqade.ir.tree_print as trp

trp.color_enabled = False


def test_var():
    assert var("a") == scalar.Variable("a")
    assert var("a") != scalar.Variable("b")

    with pytest.raises(TypeError):
        var(1)

    with pytest.raises(ValueError):
        var("a*b")

    with pytest.raises(ValidationError):
        var("__batch_params")

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
    mystdout = StringIO()
    p = PP(mystdout)
    (1 + var("a"))._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "+\n├─ Literal: 1\n⋮\n└─ Variable: a⋮\n"


def test_mul():
    mystdout = StringIO()
    p = PP(mystdout)
    (3 * var("a"))._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "*\n├─ Literal: 3\n⋮\n└─ Variable: a⋮\n"


def test_div():
    mystdout = StringIO()
    p = PP(mystdout)
    (3 / var("a"))._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "/\n├─ Literal: 3\n⋮\n└─ Variable: a⋮\n"


def test_var_member():
    va = var("a")

    assert va.children() == []
    assert va.print_node() == "Variable: a"
    assert str(va) == "a"


def test_assign_var_member():
    va = scalar.AssignedVariable("a", Decimal("1.0"))

    assert va.children() == []
    assert va.print_node() == "AssignedVariable: a = 1.0"
    assert str(va) == "a"


def test_literal_value():
    va = cast(1.0)
    with pytest.raises(TypeError):
        var(va)

    assert va.children() == []
    assert va.print_node() == "Literal: 1.0"
    assert str(va) == "1.0"


def test_invalid_keyword():
    with pytest.raises(ValidationError):
        var("__batch_params")


def test_negative_node():
    sa = cast("a")
    nsa = -sa

    assert nsa.children() == [sa]
    assert nsa.print_node() == "Negative"
    assert str(nsa) == "-(a)"


# def test_base_invalid():


def test_interval():
    itvl = scalar.Interval(start=cast(0.0), stop=cast(1.0))
    itvl_no_start = scalar.Interval(None, stop=cast(1.0))
    itvl_no_stop = scalar.Interval(start=cast(0), stop=None)
    itvl_wrong = scalar.Interval(None, None)

    assert itvl.print_node() == "Interval"

    with pytest.raises(ValueError):
        str(itvl_wrong)

    with pytest.raises(ValueError):
        itvl_wrong.children()

    assert itvl.children() == {"start": cast(0.0), "stop": cast(1.0)}
    assert itvl_no_start.children() == {"stop": cast(1.0)}
    assert itvl_no_stop.children() == {"start": cast(0)}
    assert str(itvl) == "0.0:1.0"
    assert str(itvl_no_start) == ":1.0"
    assert str(itvl_no_stop) == "0:"


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


def test_div_scalar():
    A = cast(1)
    B = cast(2)

    C = scalar.Div(A, B)

    assert C.children() == [A, B]
    assert C.print_node() == "/"

    assert C() == 0.5


def test_min_scalar():
    A = cast(1)
    B = cast(2)
    C = cast(3)

    D = scalar.Min([A, B, C])
    assert D.children() == [A, B, C]
    assert D.print_node() == "min"

    mystdout = StringIO()
    p = PP(mystdout)
    D._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "min\n├─ Literal: 1\n⋮\n├─ Literal: 2\n⋮\n└─ Literal: 3⋮\n"
    )
    assert str(D) == "min(1, 2, 3)"


def test_max_scalar():
    A = cast("a")
    B = cast("b")
    C = cast("c")

    D = scalar.Max([A, B, C])
    assert D.children() == [A, B, C]
    assert D.print_node() == "max"

    mystdout = StringIO()
    p = PP(mystdout)
    D._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "max\n├─ Literal: 1\n⋮\n├─ Literal: 2\n⋮\n└─ Literal: 3⋮\n"
    )
    assert str(D) == "max(1, 2, 3)"


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
    assert str(slc) == "(1)[5:6]"


def test_assigned_variable_methods():
    assigned_var = scalar.AssignedVariable("a", Decimal("1.0"))

    assert assigned_var.children() == []
    assert assigned_var.print_node() == "AssignedVariable: a = 1.0"
