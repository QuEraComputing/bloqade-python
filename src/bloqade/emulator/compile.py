from bloqade.ir.visitor.program_visitor import ProgramVisitor
from bloqade.ir.visitor.waveform_visitor import WaveformVisitor
from bloqade.ir.control.field import Field
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.waveform as waveform
import bloqade.ir as ir
from bloqade.ir.location.base import AtomArrangement, SiteFilling

from bloqade.emulator.space import LocalHilbertSpace, Space
from bloqade.emulator.ir import EmulatorProgram, LaserCoupling

from numpy.typing import NDArray
from typing import Any, Dict

from numbers import Number


class WaveformCompiler(WaveformVisitor):
    # TODO: implement AST generator for waveforms.

    def __init__(self, assignments: Dict[str, Number]):
        self.assignments = assignments

    def emit(self, ast: waveform.Waveform):
        # fall back on interpreter for now.
        return lambda t: ast(t, **self.assignments)


class Emulate(ProgramVisitor):
    def __init__(
        self, psi: NDArray, assignments: Dict[str, Number], blockade_radius: float = 0.0
    ):
        self.assignments = assignments
        self.psi = psi
        self.space = None
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

    def visit_register(self, ast: AtomArrangement) -> Any:
        atom_positions = []
        for loc_info in ast.enumerate():
            if loc_info.filling == SiteFilling.filled:
                atom_positions.append(loc_info.position)

        if self.hyperfine is None:
            self.space = Space(
                atom_positions,
                LocalHilbertSpace.TwoLevel,
                blockade_radius=self.blockade_radius,
            )
        else:
            self.space = Space(
                atom_positions,
                LocalHilbertSpace.ThreeLevel,
                blockade_radius=self.blockade_radius,
            )

    def emit(self, program: ir.Profram) -> EmulatorProgram:
        self.visit(program)

        return EmulatorProgram(
            register=self.space, rydberg=self.rydberg, hyperfine=self.hyperfine
        )
