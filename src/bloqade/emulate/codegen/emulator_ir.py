from bloqade.codegen.common.assignment_scan import AssignmentScan
from bloqade.ir.location.base import AtomArrangement, SiteFilling
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.control.field import (
    AssignedRunTimeVector,
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

from bloqade.emulate.ir.atom_type import ThreeLevelAtom, TwoLevelAtom
from bloqade.emulate.ir.emulator import (
    DetuningOperatorData,
    RabiOperatorData,
    RabiOperatorType,
    DetuningTerm,
    EmulatorProgram,
    Register,
    Fields,
    RabiTerm,
)

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union, List
from numbers import Number, Real
from decimal import Decimal

ParamType = Union[Real, List[Real]]


@dataclass(frozen=True)
class CompiledWaveform:
    assignments: Dict[str, Number]
    source: waveform.Waveform

    def __call__(self, t: float) -> float:
        return self.source(t, **self.assignments)


class WaveformCompiler(WaveformVisitor):
    # TODO: implement AST generator for waveforms.
    def __init__(self, assignments: Dict[str, Number] = {}):
        self.assignments = assignments

    def emit(self, ast: waveform.Waveform) -> CompiledWaveform:
        return CompiledWaveform(self.assignments, ast)


class EmulatorProgramCodeGen(AnalogCircuitVisitor):
    def __init__(
        self, assignments: Dict[str, Number] = {}, blockade_radius: Real = 0.0
    ):
        self.blockade_radius = Decimal(str(blockade_radius))
        self.assignments = assignments
        self.waveform_compiler = WaveformCompiler(assignments)
        self.geometry = None
        self.duration = 0.0
        self.drives = {}
        self.level_couplings = set()

    def visit_analog_circuit(self, ast: ir.AnalogCircuit):
        self.n_atoms = ast.register.n_atoms

        self.visit(ast.sequence)
        self.visit(ast.register)

    def visit_register(self, ast: AtomArrangement) -> Any:
        positions = []
        for loc_info in ast.enumerate():
            if loc_info.filling == SiteFilling.filled:
                position = tuple([pos(**self.assignments) for pos in loc_info.position])
                positions.append(position)

        if sequence.hyperfine in self.level_couplings:
            self.geometry = Register(
                ThreeLevelAtom, positions, blockade_radius=self.blockade_radius
            )
        else:
            self.geometry = Register(
                TwoLevelAtom, positions, blockade_radius=self.blockade_radius
            )

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                for level_coupling, sub_pulse in pulses.items():
                    self.level_couplings.add(level_coupling)
                    self.visit(sub_pulse)
                    self.drives[level_coupling] = Fields(
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
                return {atom: Decimal("1.0") for atom in range(self.n_atoms)}
            case RunTimeVector(name):
                if len(self.assignments[name]) != self.n_atoms:
                    raise ValueError(
                        f"Invalid number of atoms in '{name}' "
                        f"({len(self.assignments[name])} != {self.n_atoms})"
                    )
                return {
                    atom: Decimal(str(coeff))
                    for atom, coeff in enumerate(self.assignments[name])
                }
            case AssignedRunTimeVector(value=value, name=name):
                if len(value) != self.n_atoms:
                    raise ValueError(
                        f"Invalid number of atoms in '{name}' "
                        f"({len(value)} != {self.n_atoms})"
                    )
                return {atom: Decimal(str(coeff)) for atom, coeff in enumerate(value)}
            case ScaledLocations(locations):
                return {
                    loc.value: coeff(**self.assignments)
                    for loc, coeff in locations.items()
                }

    def visit_detuning(self, ast: Optional[Field]):
        if ast is None:
            return []

        terms = []

        match ast:
            case Field(value) if len(value) < self.n_atoms:
                for sm, wf in value.items():
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )

                    terms.append(
                        DetuningTerm(
                            operator_data=DetuningOperatorData(
                                target_atoms=self.visit_spatial_modulation(sm)
                            ),
                            amplitude=self.waveform_compiler.emit(wf),
                        )
                    )

            case Field(value):
                target_atom_dict = {
                    sm: self.visit_spatial_modulation(sm) for sm in value.keys()
                }

                for atom in range(self.n_atoms):
                    wf = sum(
                        (
                            target_atom_dict[sm].get(atom, 0.0) * wf
                            for sm, wf in value.items()
                        ),
                        start=waveform.Constant(0.0, 0.0),
                    )
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )

                    terms.append(
                        DetuningTerm(
                            operator_data=DetuningOperatorData(
                                target_atoms={atom: Decimal("1.0")}
                            ),
                            amplitude=self.waveform_compiler.emit(wf),
                        )
                    )

        return terms

    def visit_rabi(self, amplitude: Optional[Field], phase: Optional[Field]):
        terms = []

        match (amplitude, phase):
            case (None, _):
                return []

            case (Field(value), None) if len(value) < self.n_atoms:
                for sm, wf in value.items():
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )
                    terms.append(
                        RabiTerm(
                            operator_data=RabiOperatorData(
                                target_atoms=self.visit_spatial_modulation(sm),
                                operator_type=RabiOperatorType.RabiSymmetric,
                            ),
                            amplitude=self.waveform_compiler.emit(wf),
                        )
                    )

            case (Field(value), None):
                terms = []
                amplitude_target_atoms_dict = {
                    sm: self.visit_spatial_modulation(sm)
                    for sm in amplitude.value.keys()
                }
                for atom in range(self.n_atoms):
                    amplitude_wf = sum(
                        (
                            amplitude_target_atoms_dict[sm].get(atom, 0.0) * wf
                            for sm, wf in amplitude.value.items()
                        ),
                        start=waveform.Constant(0.0, 0.0),
                    )

                    self.duration = max(
                        float(amplitude_wf.duration(**self.assignments)), self.duration
                    )

                    terms.append(
                        RabiTerm(
                            operator_data=RabiOperatorData(
                                target_atoms={atom: Decimal("1.0")},
                                operator_type=RabiOperatorType.RabiSymmetric,
                            ),
                            amplitude=self.waveform_compiler.emit(amplitude_wf),
                        )
                    )

            case (
                Field(value),
                Field(value={field.Uniform: phase_waveform}),
            ) if len(value) < self.n_atoms:
                rabi_phase = self.waveform_compiler.emit(phase_waveform)
                self.duration = max(
                    float(phase_waveform.duration(**self.assignments)), self.duration
                )
                for sm, wf in value.items():
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )
                    terms.append(
                        RabiTerm(
                            operator_data=RabiOperatorData(
                                target_atoms=self.visit_spatial_modulation(sm),
                                operator_type=RabiOperatorType.RabiAsymmetric,
                            ),
                            amplitude=self.waveform_compiler.emit(wf),
                            phase=rabi_phase,
                        )
                    )

            case _:  # fully local fields
                phase_target_atoms_dict = {
                    sm: self.visit_spatial_modulation(sm) for sm in phase.value.keys()
                }
                amplitude_target_atoms_dict = {
                    sm: self.visit_spatial_modulation(sm)
                    for sm in amplitude.value.keys()
                }

                terms = []
                for atom in range(self.n_atoms):
                    phase_wf = sum(
                        (
                            phase_target_atoms_dict[sm].get(atom, 0.0) * wf
                            for sm, wf in phase.value.items()
                        ),
                        start=waveform.Constant(0.0, 0.0),
                    )

                    amplitude_wf = sum(
                        (
                            amplitude_target_atoms_dict[sm].get(atom, 0.0) * wf
                            for sm, wf in amplitude.value.items()
                        ),
                        start=waveform.Constant(0.0, 0.0),
                    )

                    self.duration = max(
                        float(amplitude_wf.duration(**self.assignments)), self.duration
                    )
                    self.duration = max(
                        float(phase_wf.duration(**self.assignments)), self.duration
                    )

                    terms.append(
                        RabiTerm(
                            operator_data=RabiOperatorData(
                                target_atoms={atom: 1},
                                operator_type=RabiOperatorType.RabiAsymmetric,
                            ),
                            amplitude=self.waveform_compiler.emit(amplitude_wf),
                            phase=self.waveform_compiler.emit(phase_wf),
                        )
                    )

        return terms

    def visit_pulse(self, ast: pulse.PulseExpr):
        match ast:
            case pulse.Pulse(fields):
                detuning = fields.get(pulse.detuning)
                amplitude = fields.get(pulse.rabi.amplitude)
                phase = fields.get(pulse.rabi.phase)

                self.detuning_terms = self.visit_detuning(detuning)
                self.rabi_terms = self.visit_rabi(amplitude, phase)

            case pulse.NamedPulse(sub_pulse, _):
                self.visit(sub_pulse)

            case _:
                raise NotImplementedError

    def emit(self, circuit: ir.AnalogCircuit) -> EmulatorProgram:
        self.assignments = AssignmentScan(self.assignments).emit(circuit.sequence)

        self.visit(circuit)
        return EmulatorProgram(
            register=self.geometry,
            duration=self.duration,
            pulses=self.drives,
        )
