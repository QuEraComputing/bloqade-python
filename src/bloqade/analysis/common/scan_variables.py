from pydantic.dataclasses import dataclass
import bloqade.ir.scalar as scalar
import bloqade.ir.control.field as field

from beartype.typing import FrozenSet

from bloqade.ir.visitor import BloqadeIRVisitor


@dataclass(frozen=True)
class ScanVariableResults:
    scalar_vars: FrozenSet[str]
    vector_vars: FrozenSet[str]
    assigned_scalar_vars: FrozenSet[str]
    assigned_vector_vars: FrozenSet[str]

    @property
    def is_assigned(self) -> bool:
        return len(self.scalar_vars) == 0 or len(self.vector_vars) == 0


class ScanVariables(BloqadeIRVisitor):
    def __init__(self):
        self.scalar_vars = set()
        self.assign_scalar_vars = set()
        self.vector_vars = set()
        self.assigned_vector_vars = set()

    def visit_scalar_Variable(self, node: scalar.Variable):
        self.scalar_vars.add(node.name)

    def visit_scalar_AssignedVariable(self, node: scalar.AssignedVariable):
        self.assign_scalar_vars.add(node.name)

    def visit_field_RunTimeVector(self, node: field.RunTimeVector):
        self.vector_vars.add(node.name)

    def visit_field_AssignedRunTimeVector(self, node: field.AssignedRunTimeVector):
        if node.name is not None:  # skip literal vectors
            self.assigned_vector_vars.add(node.name)

    def emit(self, node) -> ScanVariableResults:
        self.visit(node)
        return ScanVariableResults(
            self.scalar_vars,
            self.vector_vars,
            self.assign_scalar_vars,
            self.assigned_vector_vars,
        )
