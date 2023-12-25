from bloqade.builder.typing import LiteralType
from bloqade.ir.visitor import BloqadeIRVisitor
import bloqade.ir.control.waveform as waveform
from typing import Dict
from decimal import Decimal


class AssignmentScan(BloqadeIRVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)

    def visit_waveform_Record(self, node: waveform.Record):
        self.visit(node.waveform)
        duration = node.waveform.duration(**self.assignments)
        var = node.var

        if node.side is waveform.Side.Right:
            value = node.waveform.eval_decimal(duration, **self.assignments)
        else:
            value = node.waveform.eval_decimal(Decimal(0), **self.assignments)

        self.assignments[var.name] = value

    def emit(self, node) -> Dict[str, LiteralType]:
        self.visit(node)
        return self.assignments
