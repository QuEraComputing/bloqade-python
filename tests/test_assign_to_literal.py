from bloqade import cast
from bloqade.ir import scalar
from bloqade.rewrite.common.assign_to_literal import AssignToLiteral
from bloqade.rewrite.common.assign_variables import AssignBloqadeIR
from decimal import Decimal


def test_assign_to_literal():
    a = cast("a")
    b = cast("b")
    c = cast("c")

    expr = (a - b) * c / 2.0

    a = Decimal("1.0")
    b = Decimal("2.0")
    c = Decimal("3.0")

    assigned_expr = AssignBloqadeIR(dict(a=a, b=b, c=c)).visit(expr)

    assert AssignToLiteral().visit(assigned_expr) == scalar.Div(
        scalar.Mul(
            scalar.Add(scalar.Literal(a), scalar.Negative(scalar.Literal(b))),
            scalar.Literal(c),
        ),
        scalar.Literal(2.0),
    )
