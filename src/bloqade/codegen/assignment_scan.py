from bloqade.codegen.program_visitor import ProgramVisitor
import bloqade.ir.sequence as sequence
import bloqade.ir.pulse as pulse
import bloqade.ir.field as field
import bloqade.ir.waveform as waveform
import bloqade.ir.scalar as scalar
from numbers import Number
from typing import Dict


class AssignmentScan(ProgramVisitor):
    def __init__(self, assignments: Dict[str, Number]):
        self.assignments = dict(assignments)

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
            case pulse.NamedPulse(sub_pulse, _):
                self.visit(sub_pulse)

    def visit_field(self, ast: field.Field):
        match ast:
            case field.Field(terms):
                list(map(self.visit, terms.values()))
                list(map(self.visit, terms.keys()))

    def visit_spatial_modulation(self, ast: field.SpatialModulation):
        pass

    def visit_waveform(self, ast: waveform.Waveform):
        match ast:
            case waveform.Record(sub_waveform, scalar.Variable(name)):
                duration = sub_waveform.duration(**self.assignments)
                value = sub_waveform.eval_decimal(duration, **self.assignments)
                self.assignments[name] = value
                self.visit(sub_waveform)

            case waveform.Append(waveforms):
                list(map(self.visit, waveforms))

            case waveform.Slice(sub_waveform, _):
                self.visit(sub_waveform)

            case waveform.Add(lhs, rhs):
                self.visit(lhs)
                self.visit(rhs)

            case waveform.Negative(sub_waveform):
                self.visit(sub_waveform)

            case waveform.Scale(_, sub_waveform):
                self.visit(sub_waveform)

            case waveform.AlignedWaveform(waveform=sub_waveform):
                self.visit(sub_waveform)

            case waveform.Smooth(_, sub_waveform):
                self.visit(sub_waveform)

    def emit(self, ast: sequence.SequenceExpr) -> Dict[str, Number]:
        self.visit(ast)
        return self.assignments
