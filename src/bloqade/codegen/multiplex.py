from bloqade.codegen.program_visitor import ProgramVisitor
import bloqade.ir.sequence as sequence
import bloqade.ir.pulse as pulse
import bloqade.ir.field as field
import bloqade.ir.waveform as waveform
from typing import TYPE_CHECKING
from bloqade.task import Program

if TYPE_CHECKING:
    from bloqade.lattice.base import Lattice


class MultiplexCodeGen(ProgramVisitor):
    def __init__(self):
        self.mapping = None

    def visit_sequence(self, ast: sequence.SequenceExpr) -> sequence.SequenceExpr:
        match ast:
            case sequence.Sequence(pulses):
                list(map(self.visit, pulses.values()))
            case sequence.Append(sequences):
                list(map(self.visit, sequences))
            case sequence.Slice(sub_sequence, _):
                self.visit(sub_sequence)
            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

    def visit_pulse(self, ast: pulse.PulseExpr) -> pulse.PulseExpr:
        match ast:
            case pulse.Pulse(fields):
                new_fields = {}
                for field_name, field_ast in fields.items():
                    new_fields[field_name] = self.visit(field_ast)
                return pulse.Pulse(new_fields)

            case pulse.Append(pulses):
                return pulse.Append(list(map(self.visit, pulses)))
            case pulse.Slice(sub_pulse, interval):
                return pulse.Slice(self.visit(sub_pulse), interval)
            case pulse.NamedPulse(sub_pulse, name):
                return pulse.NamedPulse(self.visit(sub_pulse), name)

    def visit_field(self, ast: field.Field) -> field.Field:
        new_terms = {}
        for spatial_modulation, waveform_ast in ast.value.items():
            multiplex_spatial_modulation = self.visit(spatial_modulation)
            new_terms[multiplex_spatial_modulation] = self.visit(waveform_ast)

        return field.Field(new_terms)

    def visit_spatial_modulation(
        self, ast: field.SpatialModulation
    ) -> field.SpatialModulation:
        pass
        ## implmentate multiplex
        ## use self.mapping

        # return new_spatial_modulation

    def visit_waveform(self, ast: waveform.Waveform) -> waveform.Waveform:
        return ast

    def visit_lattice(self, ast: Lattice) -> Lattice:
        pass
        ## here you multiplex lattice
        ## assign self.mapping = ...
        # return new_lattice

    def emit(self, ast: Program) -> Program:
        new_lattice = self.visit(ast.lattice)
        new_seq = self.visit(ast.seq)
        return Program(new_lattice, new_seq, ast.assignments)
