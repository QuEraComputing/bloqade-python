from bloqade.ir.control.waveform import (
    AlignedWaveform,
    Constant,
    Linear,
    Poly,
    PythonFn,
    Sample,
)
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.analog_circuit import AnalogCircuit
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.analog_circuit as analog_circuit

import numbers
from typing import Any, Dict


class AssignmentScanRecord(WaveformVisitor):
    def __init__(self, assignments: Dict[str, numbers.Real] = {}):
        self.assignments = dict(assignments)

    def visit_record(self, ast: waveform.Record):
        duration = ast.waveform.duration(**self.assignments)
        var = ast.var
        value = ast.waveform(duration, **self.assignments)
        self.assignments[var.name] = value
        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append):
        list(map(self.visit, ast.waveforms))

    def visit_slice(self, ast: waveform.Slice):
        self.visit(ast.waveform)

    def visit_add(self, ast: waveform.Add):
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_negative(self, ast: waveform.Negative):
        self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale):
        self.visit(ast.waveform)

    def visit_smooth(self, ast: waveform.Smooth):
        self.visit(ast.waveform)

    def visit_sample(self, ast: Sample) -> Any:
        return self.visit(ast.waveform)

    def visit_alligned(self, ast: AlignedWaveform) -> Any:
        return super().visit_alligned(ast)

    def visit_constant(self, ast: Constant) -> Any:
        pass

    def visit_linear(self, ast: Linear) -> Any:
        pass

    def visit_poly(self, ast: Poly) -> Any:
        pass

    def visit_python_fn(self, ast: PythonFn) -> Any:
        pass

    def emit(self, ast: waveform.Waveform) -> Dict[str, numbers.Real]:
        self.visit(ast)
        return self.assignments


class AssignmentScan(AnalogCircuitVisitor):
    def __init__(self, assignments: Dict[str, numbers.Real] = {}):
        self.assignments = dict(assignments)
        self.waveform_visitor = AssignmentScanRecord(self.assignments)

    def visit_analog_circuit(self, ast: AnalogCircuit) -> Any:
        self.visit(ast.sequence)

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                list(map(self.visit, pulses.values()))
            case sequence.Append(sequences):
                list(map(self.visit, sequences))
            case sequence.Slice(sub_sequence, _):
                self.visit(sub_sequence)
            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

    def visit_pulse(self, ast: pulse.PulseExpr):
        match ast:
            case pulse.Pulse(fields):
                list(map(self.visit, fields.values()))
            case pulse.Append(pulses):
                list(map(self.visit, pulses))
            case pulse.Slice(sub_pulse, _):
                self.visit(sub_pulse)
            case pulse.NamedPulse(_, sub_pulse):
                self.visit(sub_pulse)

    def visit_field(self, ast: field.Field):
        match ast:
            case field.Field(terms):
                list(map(self.visit, terms.values()))
                list(map(self.visit, terms.keys()))

    def visit_spatial_modulation(self, ast: field.SpatialModulation):
        pass

    def visit_waveform(self, ast: waveform.Waveform):
        self.assignments.update(self.waveform_visitor.emit(ast))

    def emit(self, ast: analog_circuit.AnalogCircuit) -> Dict[str, numbers.Real]:
        self.visit(ast)
        return self.assignments
