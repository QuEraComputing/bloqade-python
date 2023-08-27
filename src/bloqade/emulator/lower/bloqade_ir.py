from bloqade.ir.location.base import AtomArrangement, SiteFilling
from bloqade.ir.visitor.program import ProgramVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.control.field import (
    Field,
    ScaledLocations,
    SpatialModulation,
    RunTimeVector,
    UniformModulation,
)
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir as ir

from bloqade.emulator.ir.space import LocalHilbertSpace, Space
from bloqade.emulator.ir.emulator_program import (
    DetuningTerm,
    EmulatorProgram,
    LaserCoupling,
    RabiTerm,
)

from typing import Any, Dict, Optional

from numbers import Number


class WaveformCompiler(WaveformVisitor):
    # TODO: implement AST generator for waveforms.

    def __init__(self, assignments: Dict[str, Number]):
        self.assignments = assignments

    def emit(self, ast: waveform.Waveform):
        # fall back on interpreter for now.
        return lambda t: ast(t, **self.assignments)


class LowerToEmulatorProgram(ProgramVisitor):
    def __init__(self, assignments: Dict[str, Number], blockade_radius: float = 0.0):
        self.assignments = assignments
        self.blockade_radius = blockade_radius
        self.space = None
        self.register = None

        self.rydberg = None
        self.hyperfine = None

    def visit_program(self, ast: ir.Program):
        self.visit(ast.register)
        self.visit(ast.sequence)

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

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                for level_coupling, sub_pulse in pulses.items():
                    self.visit(sub_pulse)
                    match level_coupling:
                        case sequence.rydberg:
                            self.rydberg = LaserCoupling(
                                level_coupling=level_coupling,
                                detuning=self.detuning_terms,
                                rabi=self.rabi_terms,
                            )
                        case sequence.hyperfine:
                            self.hyperfine = LaserCoupling(
                                level_coupling=level_coupling,
                                detuning=self.detuning_terms,
                                rabi=self.rabi_terms,
                            )

            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

            case _:
                raise NotImplementedError

    def visit_spatial_modulation(self, ast: SpatialModulation) -> Dict[int, float]:
        match ast:
            case UniformModulation():
                return {atom: 1.0 for atom in range(self.space.n_atoms)}
            case RunTimeVector(name):
                return {
                    atom: coeff for atom, coeff in enumerate(self.assignments[name])
                }
            case ScaledLocations(locations):
                return {
                    loc.value: float(coeff(**self.assignments))
                    for loc, coeff in locations.items()
                }

    def visit_detuning(self, ast: Optional[Field]):
        if ast is None:
            return []

        match ast:
            case Field(value) if len(value) < self.space.n_atoms:
                return [
                    DetuningTerm(
                        target_atoms=self.visit(sm),
                        amplitude=WaveformCompiler(self.assignments).emit(wf),
                    )
                    for sm, wf in value.items()
                ]
            case Field(value):
                target_atom_dict = {
                    sm: self.visit_spatial_modulation(sm) for sm in value.keys()
                }
                detuning_terms = []
                for atom in range(self.space.n_atoms):
                    wf = sum(
                        target_atom_dict[sm].get(atom, 0.0) * wf
                        for sm, wf in value.items()
                    )

                    detuning_terms.append(
                        DetuningTerm(target_atoms={atom: 1}, amplitude=wf)
                    )

    def visit_rabi(self, amplitude: Optional[Field], phase: Optional[Field]):
        match (amplitude, phase):
            case (None, _):
                return []

            case (Field(value), None) if len(value) < self.space.n_atoms:
                return [
                    RabiTerm(
                        target_atoms=self.visit(sm),
                        amplitude=WaveformCompiler(self.assignments).emit(wf),
                    )
                    for sm, wf in value.items()
                ]

            case (
                Field(value),
                Field(value={field.Uniform: phase_waveform}),
            ) if len(value) < self.space.n_atoms:
                rabi_phase = WaveformCompiler(self.assignments).emit(phase_waveform)
                return [
                    RabiTerm(
                        target_atoms=self.visit(sm),
                        amplitude=WaveformCompiler(self.assignments).emit(wf),
                        phase=rabi_phase,
                    )
                    for sm, wf in value.items()
                ]

            case _:  # fully local fields
                phase_target_atoms_dict = {
                    sm: self.visit_spatial_modulation(sm) for sm in phase.value.keys()
                }
                phase_target_atoms_dict = {
                    sm: self.visit_spatial_modulation(sm)
                    for sm in amplitude.value.keys()
                }

                terms = []
                for atom in range(self.space.n_atoms):
                    phase_wf = sum(
                        phase_target_atoms_dict[sm].get(atom, 0.0) * wf
                        for sm, wf in phase.value.items()
                    )
                    amplitude_wf = sum(
                        phase_target_atoms_dict[sm].get(atom, 0.0) * wf
                        for sm, wf in amplitude.value.items()
                    )
                    terms.append(
                        RabiTerm(
                            target_atoms={atom: 1},
                            amplitude=WaveformCompiler(self.assignments).emit(
                                amplitude_wf
                            ),
                            phase=WaveformCompiler(self.assignments).emit(phase_wf),
                        )
                    )

    def visit_pulse(self, ast: pulse.PulseExpr):
        match ast:
            case pulse.Pulse(fields):
                detuning = fields.get(pulse.detuning, None)
                amplitude = fields.get(pulse.rabi.amplitude, None)
                phase = fields.get(pulse.rabi.phase, None)

                self.rabi_terms = self.visit_detuning(detuning)
                self.detuning_terms = self.visit_rabi(amplitude, phase)

            case pulse.NamedPulse(sub_pulse, _):
                self.visit(sub_pulse)

            case _:
                raise NotImplementedError

    def emit(self, program: ir.Profram) -> EmulatorProgram:
        self.visit(program)

        return EmulatorProgram(
            register=self.space, rydberg=self.rydberg, hyperfine=self.hyperfine
        )
