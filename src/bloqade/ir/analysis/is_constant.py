import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence
from bloqade.builder.typing import LiteralType
from bloqade.ir.visitor import BloqadeIRVisitor

from decimal import Decimal
from beartype.typing import Any, Dict
from beartype import beartype


class IsConstant(BloqadeIRVisitor):
    @beartype
    def __init__(self, assignments: Dict[str, LiteralType] = {}) -> None:
        self.assignments = dict(assignments)
        self.is_constant = True

    def generic_visit(self, node: Any) -> Any:
        # skip visiting children if we already know it's not constant
        if not self.is_constant:
            return

        super().generic_visit(node)

    def visit_waveform_Linear(self, node: waveform.Linear):
        diff = node.stop(**self.assignments) - node.start(**self.assignments)
        self.is_constant = self.is_constant and (diff == 0)

    def visit_waveform_Poly(self, node: waveform.Poly):
        coeffs = [coeff(**self.assignments) for coeff in node.coeffs]
        if any(coeff != 0 for coeff in coeffs[1:]):
            self.is_constant = False

    def visit_waveform_PythonFn(self, node: waveform.PythonFn):
        # can't analyze python functions, assume it's not constant
        self.is_constant = False

    def visit_waveform_Append(self, node: waveform.Append):
        value = None
        for wf in node.waveforms:
            is_constant = IsConstant(self.assignments).scan(wf)

            if not is_constant:
                self.is_constant = False
                return

            if value is None:
                value = wf.eval_decimal(Decimal("0"), **self.assignments)
                new_value = value
            else:
                new_value = wf.eval_decimal(Decimal("0"), **self.assignments)

            if new_value != value:
                self.is_constant = False
                return

    def visit_waveform_Add(self, node: waveform.Add):
        left_duration = node.left.duration(**self.assignments)
        right_duration = node.right.duration(**self.assignments)

        if left_duration != right_duration:
            self.is_constant = False
            return

        self.visit(node.left)
        self.visit(node.right)

    def visit_pulse_Pulse(self, node: pulse.Pulse):
        duration = node.duration(**self.assignments)
        for val in node.fields.values():
            self.visit(val)

            if not self.is_constant:
                return

            if val.duration(**self.assignments) != duration:
                self.is_constant = False
                return

    def visit_pulse_Field(self, node: field.Field):
        duration = node.duration(**self.assignments)
        for val in node.drives.values():
            self.visit(val)

            if not self.is_constant:
                return

            if val.duration(**self.assignments) != duration:
                self.is_constant = False
                return

    def visit_sequence_Sequence(self, node: sequence.Sequence):
        duration = node.duration(**self.assignments)
        for val in node.pulses.values():
            self.visit(val)

            if not self.is_constant:
                return

            if val.duration(**self.assignments) != duration:
                self.is_constant = False
                return

    def scan(self, node) -> bool:
        self.visit(node)
        return self.is_constant
