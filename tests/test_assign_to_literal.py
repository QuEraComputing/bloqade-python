from bloqade import cast, constant
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

    wf_expr = constant(1.0, expr)

    new_expr = AssignBloqadeIR(dict(a=a, b=b, c=c)).visit(wf_expr)
    literal_expr = AssignToLiteral().visit(new_expr)

    assert cast((a - b) * c / Decimal("2.0")) == literal_expr.value
