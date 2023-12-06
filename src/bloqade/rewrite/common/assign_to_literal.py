from beartype.typing import Any
from bloqade.ir.visitor import BloqadeIRTransformer
import bloqade.ir.scalar as scalar


class AssignToLiteral(BloqadeIRTransformer):
    """Transform all assigned variables to literals."""

    def visit_scalar_AssignedVariable(self, node: scalar.AssignedVariable):
        return scalar.Literal(node.value)

    def visit(self, node: Any) -> Any:
        if isinstance(node, scalar.Scalar):
            return scalar.Scalar.canonicalize(super().visit(node))

        return super().visit(node)
