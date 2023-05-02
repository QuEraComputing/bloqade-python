from bloqade.codegen.hardware.field import FieldCodeGen
from bloqade.ir.field import Field

from bloqade.ir.sequence import (
    LevelCoupling,
    RydbergLevelCoupling,
    HyperfineLevelCoupling,
)
from bloqade.ir.pulse import PulseExpr, Pulse, NamedPulse
from bloqade.ir.pulse import RabiFrequencyAmplitude, RabiFrequencyPhase, Detuning

from pydantic.dataclasses import dataclass
from typing import Optional

import quera_ahs_utils.quera_ir.task_specification as task_spec


@dataclass
class PulseCodeGen(FieldCodeGen):
    level_coupling: Optional[LevelCoupling] = None
    rabi_frequency_amplitude: Optional[task_spec.RabiFrequencyAmplitude] = None
    rabi_frequency_phase: Optional[task_spec.RabiFrequencyPhase] = None
    detuning: Optional[task_spec.Detuning] = None

    def assignment_scan(self, ast: PulseExpr):
        match ast:
            case Pulse(value):
                self.field_name = RabiFrequencyAmplitude()
                if self.field_name in value:
                    FieldCodeGen(
                        self.n_atoms,
                        self.assignments,
                        field_name=RabiFrequencyAmplitude(),
                    ).assignment_scan(value[self.field_name])

                self.field_name = RabiFrequencyPhase()
                if self.field_name in value:
                    new_assignments = FieldCodeGen(
                        self.n_atoms,
                        self.assignments,
                        field_name=RabiFrequencyPhase(),
                    ).assignment_scan(value[self.field_name])

                self.field_name = Detuning()
                if self.field_name in value:
                    new_assignments = FieldCodeGen(
                        self.n_atoms,
                        self.assignments,
                        field_name=Detuning(),
                    ).assignment_scan(value[self.field_name])

            case NamedPulse(pulse=pulse):
                self.assignment_scan(pulse)

            case _:
                # TODO: Improve error message here
                raise NotImplementedError

        return new_assignments

    def scan(self, ast: PulseExpr):
        match ast:
            case Pulse(value):
                self.field_name = RabiFrequencyAmplitude()
                if self.field_name in value:
                    self.rabi_frequency_amplitude = FieldCodeGen(
                        self.n_atoms,
                        self.assignments,
                        field_name=RabiFrequencyAmplitude(),
                    ).emit(value[self.field_name])

                self.field_name = RabiFrequencyPhase()
                if self.field_name in value:
                    self.rabi_frequency_phase = FieldCodeGen(
                        self.n_atoms,
                        self.assignments,
                        field_name=RabiFrequencyPhase(),
                    ).emit(value[self.field_name])

                self.field_name = Detuning()
                if self.field_name in value:
                    self.detuning = FieldCodeGen(
                        self.n_atoms,
                        self.assignments,
                        field_name=Detuning(),
                    ).emit(value[self.field_name])

            case _:
                # TODO: Improve error message here
                raise NotImplementedError

        match (self.rabi_frequency_amplitude, self.rabi_frequency_phase, self.detuning):
            case (
                task_spec.RabiFrequencyAmplitude(),
                task_spec.RabiFrequencyPhase(),
                task_spec.Detuning(),
            ):
                pass

            case (
                task_spec.RabiFrequencyAmplitude(),
                task_spec.RabiFrequencyPhase(),
                None,
            ):
                duration = self.rabi_frequency_amplitude.global_.times[-1]
                self.detuning = task_spec.Detuning(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )

            case (task_spec.RabiFrequencyAmplitude(), None, task_spec.Detuning()):
                duration = self.rabi_frequency_amplitude.global_.times[-1]
                self.rabi_frequency_phase = task_spec.RabiFrequencyPhase(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )

            case (None, task_spec.RabiFrequencyPhase(), task_spec.Detuning()):
                duration = self.rabi_frequency_phase.global_.times[-1]
                self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )

            case (task_spec.RabiFrequencyAmplitude(), None, None):
                duration = self.rabi_frequency_amplitude.global_.times[-1]
                self.detuning = task_spec.Detuning(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )
                self.rabi_frequency_phase = task_spec.RabiFrequencyPhase(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )

            case (None, task_spec.RabiFrequencyPhase(), None):
                duration = self.rabi_frequency_phase.global_.times[-1]
                self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )
                self.detuning = task_spec.Detuning(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )

            case (None, None, task_spec.Detuning()):
                duration = self.detuning.global_.times[-1]
                self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )
                self.rabi_frequency_phase = task_spec.RabiFrequencyPhase(
                    global_=task_spec.GlobalField(
                        times=[0, duration], values=[0.0, 0.0]
                    )
                )

            case _:
                raise ValueError("No fields provided to convert to QuEra AHS program")

    def emit(self, ast: PulseExpr):
        match self.level_coupling:
            case RydbergLevelCoupling():
                self.scan(ast)
                return task_spec.RydbergHamiltonian(
                    rabi_frequency_amplitude=self.rabi_frequency_amplitude,
                    rabi_frequency_phase=self.rabi_frequency_phase,
                    detuning=self.detuning,
                )
            case HyperfineLevelCoupling():
                raise ValueError("QuEra AHS program doesn't support Hyperfine levels")

            case _:
                raise RuntimeError(
                    "Fatal error: failed to compile Pulse to QuEra AHS program. "
                )
