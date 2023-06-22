from bloqade.codegen.emulator.space import Space
from bloqade.ir.visitor.program_visitor import ProgramVisitor
from bloqade.ir.visitor.waveform_visitor import WaveformVisitor
from bloqade.ir.control.field import Field
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir as ir
from bloqade.ir.location.base import SiteFilling

from pydantic.dataclasses import dataclass
from numpy.typing import NDArray, List, Tuple, Callable
from typing import TYPE_CHECKING, Any, Dict, Optional
from numbers import Number


if TYPE_CHECKING:
    from bloqade.ir.location.base import AtomArrangement


@dataclass
class RabiDrive:
    amplitude: Dict[field.SpatialModulation, Callable[float, float]] = {}
    phase: Dict[field.SpatialModulation, Callable[float, float]] = {}


@dataclass
class LaserCoupling:
    detuning: Dict[field.SpatialModulation, Callable[float, float]] = {}
    rabi: RabiDrive = RabiDrive()


@dataclass
class EmulatorProgram:
    space: Space
    register: List[Tuple[float, float]]
    rydberg: Optional[LaserCoupling]
    hyperfine: Optional[LaserCoupling]


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
        self.current_coupling = None
        self.current_field = None
        self.register = None
        self.rydberg = None
        self.hyperfine = None

    def visit_program(self, ast: ir.Program):
        self.visit(ast.register)
        self.visit(ast.sequence)

    def visit_atom_arrangement(self, ast: AtomArrangement):
        self.register = [
            loc_info.position
            for loc_info in ast.enumerate()
            if loc_info.filling == SiteFilling.filled
        ]

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                for level_coupling, sub_pulse in pulses.items():
                    self.current_coupling = LaserCoupling()
                    self.visit(sub_pulse)

                    match level_coupling:
                        case sequence.rydberg:
                            self.rydberg = self.current_coupling
                        case sequence.hyperfine:
                            self.hyperfine = self.current_coupling

            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

            case _:
                raise NotImplementedError

    def visit_pulse(self, ast: pulse.PulseExpr):
        match ast:
            case pulse.Pulse(fields):
                for field_name, sub_field in fields.items():
                    match field_name:
                        case pulse.rabi.amplitude:
                            self.current_field = self.current_coupling.rabi.amplitude
                        case pulse.rabi.phase:
                            self.current_field = self.current_coupling.rabi.phase
                        case pulse.detuning:
                            self.current_field = self.current_coupling.detuning

                    self.visit(sub_field)

            case pulse.NamedPulse(sub_pulse, _):
                self.visit(sub_pulse)

            case _:
                raise NotImplementedError

    def visit_field(self, ast: Field) -> Any:
        for sp_mod, wf in ast.value.items():
            self.current_field[sp_mod] = WaveformCompiler(self.assignments).emit(wf)

    def emit(self, program: ir.Profram) -> EmulatorProgram:
        self.visit(program)

        return EmulatorProgram(
            register=self.register, rydberg=self.rydberg, hyperfine=self.hyperfine
        )
