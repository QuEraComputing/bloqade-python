from bloqade.codegen.program_visitor import ProgramVisitor
import bloqade.ir.sequence as sequence
import bloqade.ir.pulse as pulse
import bloqade.ir.field as field
import bloqade.ir.waveform as waveform
from numbers import Number
from typing import Dict


class AssignmentScan(ProgramVisitor):
    def __init__(self, assignments: Dict[str, Number]):
        self.assignments = dict(assignments)
        self.sequence_programs = []
        self.pulse_programs = []
        self.amplitude_terms = []
        self.phase_terms = []
        self.detuning_terms = []

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                if sequence.hyperfine in pulses:
                    raise NotImplementedError

                self.visit(pulses[sequence.rydberg])

            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

            case _:
                raise NotImplementedError

    def visit_pulse(self, ast: pulse.PulseExpr):
        match ast:
            case pulse.Pulse(fields):
                self.field_name = pulse.rabi.amplitude
                field = fields.get(self.field_name)
                if field:
                    self.visit(field)

                self.field_name = pulse.rabi.phase
                field = fields.get(self.field_name)
                if field:
                    self.visit(field)

                self.field_name = pulse.detuning
                field = fields.get(self.field_name)
                if field:
                    self.visit(field)

            case pulse.NamedPulse(sub_pulse, _):
                self.visit(sub_pulse)

            case _:
                raise NotImplementedError

    def visit_field(self, ast: field.Field):
        match ast:
            case field.Field(terms) if len(terms) < self.n_atoms:
                list(map(self.visit, terms.values()))
                list(map(self.visit, terms.keys()))

    def visit_spatial_modulation(self, ast: field.SpatialModulation):
        raise NotImplementedError

    def visit_waveform(self, ast: waveform.Waveform):
        raise NotImplementedError

    def emit(self, ast: sequence.SequenceExpr) -> Dict[str, Number]:
        self.visit(ast)
        return self.assignments
