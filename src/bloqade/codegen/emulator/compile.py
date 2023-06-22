from bloqade.codegen.emulator.space import Space
from bloqade.ir.visitor.program_visitor import ProgramVisitor
from bloqade.ir.visitor.waveform_visitor import WaveformVisitor
from bloqade.ir.control.field import Field
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform

from pydantic.dataclasses import dataclass
from numpy.typing import NDArray
from typing import TYPE_CHECKING, Any, Dict, Callable
from numbers import Number


if TYPE_CHECKING:
    from bloqade.ir.location.base import AtomArrangement


@dataclass(frozen=True)
class CouplingSpatialModulation:
    field_name: field.FieldName
    level_coupling: sequence.LevelCoupling
    spatial_modulation: field.SpatialModulation


@dataclass
class EmulatorProgram:
    terms: Dict[CouplingSpatialModulation, Callable]


class WaveformCompiler(WaveformVisitor):
    # TODO: implement AST generator for waveforms.

    def __init__(self, assignments: Dict[str, Number]):
        self.assignments = assignments

    def emit(self, ast: waveform.Waveform):
        # fall back on interpreter for now.
        return lambda t: ast(t, **self.assignments)


class Emulate(ProgramVisitor):
    def __init__(self, psi: NDArray, space: Space, assignments: Dict[str, Number]):
        self.assignments = assignments
        self.psi = psi
        self.space = space
        self.terms = {}

    def visit_atom_arrangement(self, ast: AtomArrangement):
        # generate rydberg interaction.
        pass

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                for level_coupling, sub_pulse in pulses.items():
                    self.level_coupling = level_coupling
                    self.visit(sub_pulse)

            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

            case _:
                raise NotImplementedError

    def visit_pulse(self, ast: pulse.PulseExpr):
        match ast:
            case pulse.Pulse(fields):
                for field_name, sub_field in fields.items():
                    self.field_name = field_name
                    self.visit(sub_field)

            case pulse.NamedPulse(sub_pulse, _):
                self.visit(sub_pulse)

            case _:
                raise NotImplementedError

    def visit_field(self, ast: Field) -> Any:
        for spatial_modulation, sub_waveform in ast.value.items():
            compiled_waveform = WaveformCompiler(self.assignments).emit(sub_waveform)

            key = CouplingSpatialModulation(
                self.field_name, self.level_coupling, spatial_modulation
            )

            self.terms[key] = compiled_waveform
