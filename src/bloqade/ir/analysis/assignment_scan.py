from bloqade.builder.typing import LiteralType
from bloqade.ir.visitor.base import BloqadeIRVisitor
import bloqade.ir.control.waveform as waveform
from typing import Dict


class AssignmentScan(BloqadeIRVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)

    def visit_waveform_Record(self, node: waveform.Record):
        self.visit(node.waveform)
        duration = node.waveform.duration(**self.assignments)
        var = node.var
        value = node.waveform.eval_decimal(duration, **self.assignments)
        self.assignments[var.name] = value

    def emit(self, node) -> Dict[str, LiteralType]:
        self.visit(node)
        return self.assignments
