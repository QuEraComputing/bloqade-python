import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.builder.typing import LiteralType
from bloqade.ir.visitor import BloqadeIRTransformer
from typing import Any, Dict


class AssignBloqadeIR(BloqadeIRTransformer):
    def __init__(self, mapping: Dict[str, LiteralType]):
        self.mapping = dict(mapping)

    def visit_scalar_Variable(self, node: scalar.Variable):
        if node.name in self.mapping:
            return scalar.AssignedVariable(node.name, self.mapping[node.name])

        return node

    def visit_scalar_AssignedVariable(self, node: scalar.AssignedVariable):
        if node.name in self.mapping:
            raise ValueError(f"Variable {node.name} already assigned to {node.value}.")

        return node

    def visit_field_RunTimeVector(self, node: field.RunTimeVector):
        if node.name in self.mapping:
            return field.AssignedRunTimeVector(node.name, self.mapping[node.name])

        return node

    def visit_waveform_Record(self, node: waveform.Record):
        if node.var.name in self.mapping:
            return self.visit(node.waveform)

        return waveform.Record(self.visit(node.waveform), node.var)

    def visit_field_AssignedRunTimeVector(self, node: field.AssignedRunTimeVector):
        if node.name in self.mapping:
            raise ValueError(f"Variable {node.name} already assigned to {node.value}.")

        return node

    def emit(self, node) -> Any:
        return self.visit(node)
