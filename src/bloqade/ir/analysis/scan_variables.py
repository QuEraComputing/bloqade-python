from pydantic.dataclasses import dataclass
import bloqade.ir.scalar as scalar
import bloqade.ir.control.field as field

from beartype.typing import FrozenSet

from bloqade.ir.visitor import BloqadeIRVisitor


@dataclass(frozen=True)
class ScanVariableResults:
    scalar_vars: FrozenSet[str]
    vector_vars: FrozenSet[str]


class ScanVariables(BloqadeIRVisitor):
    def __init__(self):
        self.scalar_vars = set()
        self.vector_vars = set()

    def visit_scalar_Variable(self, node: scalar.Variable):
        self.scalar_vars.add(node.name)

    def visit_field_RunTimeVector(self, node: field.RunTimeVector):
        self.vector_vars.add(node.name)

    def emit(self, node) -> ScanVariableResults:
        self.visit(node)
        return ScanVariableResults(self.scalar_vars, self.vector_vars)
