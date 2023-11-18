from beartype.typing import Any, Dict, Optional
from bloqade.builder.typing import LiteralType
from bloqade.ir.location.location import AtomArrangement, SiteFilling
from bloqade.ir.visitor.base import BloqadeIRVisitor
from bloqade.ir.analysis.assignment_scan import AssignmentScan
from bloqade.ir.analysis.is_hyperfine import IsHyperfineSequence


import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
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
from decimal import Decimal


class EmulatorProgramCodeGen(BloqadeIRVisitor):
    def __init__(
        self,
        assignments: Dict[str, LiteralType] = {},
        blockade_radius: Decimal = 0.0,
        use_hyperfine: bool = False,
    ):
        self.blockade_radius = Decimal(str(blockade_radius))
        self.assignments = assignments
        self.register = None
        self.duration = 0.0
        self.pulses = {}
        self.level_couplings = set()
        self.original_index = []
        self.is_hyperfine = use_hyperfine

    def compile_waveform(self, ast: waveform.Waveform) -> CompiledWaveform:
        return CompiledWaveform(self.assignments, ast)

    def construct_register(self, ast: AtomArrangement) -> Any:
        positions = []
        for org_index, loc_info in enumerate(ast.enumerate()):
            if loc_info.filling == SiteFilling.filled:
                position = tuple([pos(**self.assignments) for pos in loc_info.position])
                positions.append(position)
                self.original_index.append(org_index)

        if self.is_hyperfine:
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

    def construct_detuning(self, ast: Optional[field.Field]):
        if ast is None:
            return []

        terms = []

        if len(ast.drives) <= self.n_atoms:
            for sm, wf in ast.drives.items():
                self.duration = max(
                    float(wf.duration(**self.assignments)), self.duration
                )

                terms.append(
                    DetuningTerm(
                        operator_data=DetuningOperatorData(target_atoms=self.visit(sm)),
                        amplitude=self.compile_waveform(wf),
                    )
                )
        else:
            target_atom_dict = {sm: self.visit(sm) for sm in ast.drives.keys()}

            for atom in range(self.n_atoms):
                if not any(atom in value for value in target_atom_dict.values()):
                    continue

                wf = sum(
                    (
                        target_atom_dict[sm][atom] * wf
                        for sm, wf in ast.drives.items()
                        if atom in target_atom_dict[sm]
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
                        amplitude=self.compile_waveform(wf),
                    )
                )

        return terms

    def construct_rabi(
        self, amplitude: Optional[field.Field], phase: Optional[field.Field]
    ):
        terms = []

        if amplitude is None:
            return terms

        if phase is None and len(amplitude.drives) <= self.n_atoms:
            for sm, wf in amplitude.drives.items():
                self.duration = max(
                    float(wf.duration(**self.assignments)), self.duration
                )

                target_atoms = self.visit(sm)

                if len(target_atoms) == 0:
                    continue
                elif len(target_atoms) == 1:
                    (scale,) = target_atoms.values()
                    if scale != 1:
                        wf = scale * wf

                terms.append(
                    RabiTerm(
                        operator_data=RabiOperatorData(
                            target_atoms=target_atoms,
                            operator_type=RabiOperatorType.RabiSymmetric,
                        ),
                        amplitude=self.compile_waveform(wf),
                    )
                )
        elif phase is None:  # fully local real rabi fields
            amplitude_target_atoms_dict = {
                sm: self.visit(sm) for sm in amplitude.drives.keys()
            }
            for atom in range(self.n_atoms):
                if not any(
                    atom in value for value in amplitude_target_atoms_dict.values()
                ):
                    continue

                amplitude_wf = sum(
                    (
                        amplitude_target_atoms_dict[sm][atom] * wf
                        for sm, wf in amplitude.drives.items()
                        if atom in amplitude_target_atoms_dict[sm]
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
                        amplitude=self.compile_waveform(amplitude_wf),
                    )
                )
        elif (
            len(phase.drives) == 1
            and field.UniformModulation() in phase.drives
            and len(amplitude.drives) <= self.n_atoms
        ):
            (phase_waveform,) = phase.drives.values()
            rabi_phase = self.compile_waveform(phase_waveform)
            self.duration = max(
                float(phase_waveform.duration(**self.assignments)), self.duration
            )
            for sm, wf in amplitude.drives.items():
                self.duration = max(
                    float(wf.duration(**self.assignments)), self.duration
                )

                target_atoms = self.visit(sm)

                if len(target_atoms) == 0:
                    continue
                elif len(target_atoms) == 1:
                    (scale,) = target_atoms.values()
                    if scale != 1:
                        wf = scale * wf

                terms.append(
                    RabiTerm(
                        operator_data=RabiOperatorData(
                            target_atoms=target_atoms,
                            operator_type=RabiOperatorType.RabiAsymmetric,
                        ),
                        amplitude=self.compile_waveform(wf),
                        phase=rabi_phase,
                    )
                )
        else:
            phase_target_atoms_dict = {sm: self.visit(sm) for sm in phase.drives.keys()}
            amplitude_target_atoms_dict = {
                sm: self.visit(sm) for sm in amplitude.drives.keys()
            }

            terms = []
            for atom in range(self.n_atoms):
                if not any(
                    atom in value for value in amplitude_target_atoms_dict.values()
                ):
                    continue

                phase_wf = sum(
                    (
                        phase_target_atoms_dict[sm][atom] * wf
                        for sm, wf in phase.drives.items()
                        if atom in phase_target_atoms_dict[sm]
                    ),
                    start=waveform.Constant(0.0, 0.0),
                )

                amplitude_wf = sum(
                    (
                        amplitude_target_atoms_dict[sm][atom] * wf
                        for sm, wf in amplitude.drives.items()
                        if atom in amplitude_target_atoms_dict[sm]
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
                        amplitude=self.compile_waveform(amplitude_wf),
                        phase=self.compile_waveform(phase_wf),
                    )
                )

        return terms

    #######################################
    #          AST Visitor Methods        #
    #######################################

    def generic_visit(self, node: Any) -> Any:
        if isinstance(node, AtomArrangement):
            self.construct_register(node)

        super().generic_visit(node)

    def visit_analog_circuit_AnalogCircuit(self, ast: ir.AnalogCircuit):
        self.visit(ast.register)
        self.visit(ast.sequence)

    def visit_sequence_Sequence(self, ast: sequence.Sequence) -> None:
        level_coupling_mapping = {
            sequence.hyperfine: LevelCoupling.Hyperfine,
            sequence.rydberg: LevelCoupling.Rydberg,
        }
        for level_coupling, sub_pulse in ast.pulses.items():
            self.visit(sub_pulse)
            self.pulses[level_coupling_mapping[level_coupling]] = Fields(
                detuning=self.detuning_terms,
                rabi=self.rabi_terms,
            )

    def visit_sequence_NamedSequence(self, ast: sequence.NamedSequence) -> None:
        self.vicit(ast.sequence)

    def visit_sequence_Slice(self, ast: sequence.Slice) -> None:
        raise NotImplementedError("Slice sequences are not supported by the emulator.")

    def visit_sequence_Append(self, ast: sequence.Append) -> None:
        raise NotImplementedError("Append sequences are not supported by the emulator.")

    def visit_pulse_Pulse(self, ast: pulse.Pulse) -> None:
        detuning = ast.fields.get(pulse.detuning)
        amplitude = ast.fields.get(pulse.rabi.amplitude)
        phase = ast.fields.get(pulse.rabi.phase)

        self.detuning_terms = self.construct_detuning(detuning)
        self.rabi_terms = self.construct_rabi(amplitude, phase)

    def visit_pulse_NamedPulse(self, ast: pulse.NamedPulse) -> Any:
        self.visit(ast.pulse)

    def visit_pulse_Slice(self, ast: pulse.Slice) -> Any:
        raise NotImplementedError("Slice pulses are not supported by the emulator.")

    def visit_pulse_Append(self, ast: pulse.Append) -> Any:
        raise NotImplementedError("Append pulses are not supported by the emulator.")

    def visit_field_UniformModulation(
        self, ast: field.UniformModulation
    ) -> Dict[int, Decimal]:
        return {atom: Decimal("1.0") for atom in range(self.n_atoms)}

    def visit_field_RunTimeVector(self, ast: field.RunTimeVector) -> Dict[int, Decimal]:
        value = self.assignments[ast.name]
        return {
            new_index: Decimal(str(value[original_index]))
            for new_index, original_index in enumerate(self.original_index)
            if value[original_index] != 0
        }

    def visit_field_AssignedRunTimeVector(
        self, ast: field.AssignedRunTimeVector
    ) -> Dict[int, Decimal]:
        return {
            new_index: Decimal(str(ast.value[original_index]))
            for new_index, original_index in enumerate(self.original_index)
            if ast.value[original_index] != 0
        }

    def visit_field_ScaledLocations(
        self, ast: field.ScaledLocations
    ) -> Dict[int, Decimal]:
        target_atoms = {}

        for location in ast.value.keys():
            if location.value >= self.n_sites or location.value < 0:
                raise ValueError(
                    f"Location {location.value} is out of bounds for register with "
                    f"{self.n_sites} sites."
                )

        for new_index, original_index in enumerate(self.original_index):
            value = ast.value.get(field.Location(original_index))
            if value is not None and value != 0:
                target_atoms[new_index] = value(**self.assignments)

        return target_atoms

    def emit(self, circuit: ir.AnalogCircuit) -> EmulatorProgram:
        self.assignments = AssignmentScan(self.assignments).emit(circuit.sequence)
        self.is_hyperfine = IsHyperfineSequence().emit(circuit) or self.is_hyperfine
        self.n_atoms = circuit.register.n_atoms
        self.n_sites = circuit.register.n_sites

        self.visit(circuit)
        return EmulatorProgram(
            register=self.register,
            duration=self.duration,
            pulses=self.pulses,
        )
