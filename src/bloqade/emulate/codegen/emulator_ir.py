from bloqade.codegen.common.assignment_scan import AssignmentScan
from bloqade.ir.location.base import AtomArrangement, SiteFilling
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.control.field import (
    AssignedRunTimeVector,
    Field,
    ScaledLocations,
    RunTimeVector,
    UniformModulation,
)
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
import bloqade.ir as ir

from bloqade.emulate.ir.atom_type import ThreeLevelAtom, TwoLevelAtom
from bloqade.emulate.ir.emulator import (
    DetuningOperatorData,
    LevelCoupling,
    RabiOperatorData,
    RabiOperatorType,
    DetuningTerm,
    CompiledWaveform,
    EmulatorProgram,
    Register,
    Fields,
    RabiTerm,
)

from typing import Any, Dict, Optional, Union, List
from numbers import Number, Real
from decimal import Decimal

ParamType = Union[Real, List[Real]]


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
        self.register = None
        self.duration = 0.0
        self.pulses = {}
        self.level_couplings = set()
        self.original_index = []

    def visit_analog_circuit(self, ast: ir.AnalogCircuit):
        self.n_atoms = ast.register.n_atoms
        self.n_sites = ast.register.n_sites

        self.visit(ast.sequence)
        self.visit(ast.register)

    def visit_register(self, ast: AtomArrangement) -> Any:
        positions = []
        for original_index, loc_info in enumerate(ast.enumerate()):
            if loc_info.filling == SiteFilling.filled:
                position = tuple([pos(**self.assignments) for pos in loc_info.position])
                positions.append(position)
                self.original_index.append(original_index)

        if sequence.hyperfine in self.level_couplings:
            self.register = Register(
                ThreeLevelAtom,
                positions,
                blockade_radius=self.blockade_radius,
            )
        else:
            self.register = Register(
                TwoLevelAtom,
                positions,
                blockade_radius=self.blockade_radius,
            )

    def visit_sequence(self, ast: sequence.Sequence) -> None:
        level_coupling_mapping = {
            sequence.hyperfine: LevelCoupling.Hyperfine,
            sequence.rydberg: LevelCoupling.Rydberg,
        }
        for level_coupling, sub_pulse in ast.pulses.items():
            self.level_couplings.add(level_coupling)
            self.visit(sub_pulse)
            self.pulses[level_coupling_mapping[level_coupling]] = Fields(
                detuning=self.detuning_terms,
                rabi=self.rabi_terms,
            )

    def visit_named_sequence(self, ast: sequence.NamedSequence) -> None:
        self.vicit(ast.sequence)

    def visit_slice_sequence(self, ast: sequence.Slice) -> None:
        raise NotImplementedError("Slice sequences are not supported by the emulator.")

    def visit_append_sequence(self, ast: sequence.Append) -> None:
        raise NotImplementedError("Append sequences are not supported by the emulator.")

    def visit_pulse(self, ast: pulse.Pulse) -> None:
        detuning = ast.fields.get(pulse.detuning)
        amplitude = ast.fields.get(pulse.rabi.amplitude)
        phase = ast.fields.get(pulse.rabi.phase)

        self.detuning_terms = self.visit_detuning(detuning)
        self.rabi_terms = self.visit_rabi(amplitude, phase)

    def visit_named_pulse(self, ast: pulse.NamedPulse) -> Any:
        self.visit(ast.pulse)

    def visit_slice_pulse(self, ast: pulse.Slice) -> Any:
        raise NotImplementedError("Slice pulses are not supported by the emulator.")

    def visit_append_pulse(self, ast: pulse.Append) -> Any:
        raise NotImplementedError("Append pulses are not supported by the emulator.")

    def visit_uniform_modulation(self, ast: UniformModulation) -> Dict[int, Decimal]:
        return {atom: Decimal("1.0") for atom in range(self.n_atoms)}

    def visit_run_time_vector(self, ast: RunTimeVector) -> Dict[int, Decimal]:
        value = self.assignments[ast.name]
        return {
            new_index: Decimal(str(value[original_index]))
            for new_index, original_index in enumerate(self.original_index)
        }

    def visit_assigned_run_time_vector(
        self, ast: AssignedRunTimeVector
    ) -> Dict[int, Decimal]:
        return {
            new_index: Decimal(str(ast.value[original_index]))
            for new_index, original_index in enumerate(self.original_index)
        }

    def visit_scaled_locations(self, ast: ScaledLocations) -> Dict[int, Decimal]:
        target_atoms = {}

        for location in ast.value.keys():
            if location.value >= self.n_sites or location.value < 0:
                raise ValueError(
                    f"Location {location.value} is out of bounds for register with "
                    f"{self.n_sites} sites."
                )

        for new_index, original_index in enumerate(self.original_index):
            value = ast.value.get(original_index, scalar.Literal(0))
            target_atoms[new_index] = value(**self.assignments)

        return target_atoms

    def visit_detuning(self, ast: Optional[Field]):
        if ast is None:
            return []

        terms = []

        if len(ast.value) <= self.n_atoms:
            for sm, wf in ast.value.items():
                self.duration = max(
                    float(wf.duration(**self.assignments)), self.duration
                )

                terms.append(
                    DetuningTerm(
                        operator_data=DetuningOperatorData(target_atoms=self.visit(sm)),
                        amplitude=self.waveform_compiler.emit(wf),
                    )
                )
        else:
            target_atom_dict = {sm: self.visit(sm) for sm in ast.value.keys()}

            for atom in range(self.n_atoms):
                wf = sum(
                    (
                        target_atom_dict[sm].get(atom, 0.0) * wf
                        for sm, wf in ast.value.items()
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

        if amplitude is None:
            return terms

        if phase is None and len(amplitude.value) <= self.n_atoms:
            for sm, wf in amplitude.value.items():
                self.duration = max(
                    float(wf.duration(**self.assignments)), self.duration
                )
                terms.append(
                    RabiTerm(
                        operator_data=RabiOperatorData(
                            target_atoms=self.visit(sm),
                            operator_type=RabiOperatorType.RabiSymmetric,
                        ),
                        amplitude=self.waveform_compiler.emit(wf),
                    )
                )
        elif phase is None:  # fully local real rabi fields
            amplitude_target_atoms_dict = {
                sm: self.visit(sm) for sm in amplitude.value.keys()
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
        elif (
            len(phase.value) == 1
            and UniformModulation() in phase.value
            and len(amplitude.value) <= self.n_atoms
        ):
            (phase_waveform,) = phase.value.values()
            rabi_phase = self.waveform_compiler.emit(phase_waveform)
            self.duration = max(
                float(phase_waveform.duration(**self.assignments)), self.duration
            )
            for sm, wf in amplitude.value.items():
                self.duration = max(
                    float(wf.duration(**self.assignments)), self.duration
                )
                terms.append(
                    RabiTerm(
                        operator_data=RabiOperatorData(
                            target_atoms=self.visit(sm),
                            operator_type=RabiOperatorType.RabiAsymmetric,
                        ),
                        amplitude=self.waveform_compiler.emit(wf),
                        phase=rabi_phase,
                    )
                )
        else:
            phase_target_atoms_dict = {sm: self.visit(sm) for sm in phase.value.keys()}
            amplitude_target_atoms_dict = {
                sm: self.visit(sm) for sm in amplitude.value.keys()
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

    def emit(self, circuit: ir.AnalogCircuit) -> EmulatorProgram:
        self.assignments = AssignmentScan(self.assignments).emit(circuit.sequence)

        self.visit(circuit)
        return EmulatorProgram(
            register=self.register,
            duration=self.duration,
            pulses=self.pulses,
        )
