from bloqade.codegen.hardware.field import FieldCodeGen

from bloqade.ir.sequence import LevelCoupling
from bloqade.ir.pulse import PulseExpr, Pulse
from bloqade.ir.pulse import FieldName

from pydantic.dataclasses import dataclass
from typing import Optional

from quera_ahs_utils.quera_ir.task_specification import (
    RydbergHamiltonian,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
    Detuning,
    GlobalField,
)


@dataclass
class PulseCodeGen(FieldCodeGen):
    level_coupling: Optional[LevelCoupling] = None
    rabi_frequency_amplitude: Optional[RabiFrequencyAmplitude] = None
    rabi_frequency_phase: Optional[RabiFrequencyPhase] = None
    detuning: Optional[Detuning] = None

    def scan(self, ast: PulseExpr):
        match ast:
            case Pulse(value):
                self.field_name = FieldName.RabiFrequencyAmplitude
                if self.field_name in value:
                    self.rabi_frequency_amplitude = FieldCodeGen.emit(
                        self, value[self.field_name]
                    )

                self.field_name = FieldName.RabiFrequencyPhase
                if self.field_name in value:
                    self.rabi_frequency_phase = FieldCodeGen.emit(
                        self, value[self.field_name]
                    )

                self.field_name = FieldName.Detuning
                if self.field_name in value:
                    self.detuning = FieldCodeGen.emit(self, value[self.field_name])

            case _:
                # TODO: Improve error message here
                raise NotADirectoryError

        match (self.rabi_frequency_amplitude, self.rabi_frequency_phase, self.detuning):
            case (RabiFrequencyAmplitude(), RabiFrequencyPhase(), Detuning()):
                pass

            case (RabiFrequencyAmplitude(), RabiFrequencyPhase(), None):
                duration = self.rabi_frequency_amplitude.global_.times[-1]
                self.detuning = Detuning(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )

            case (RabiFrequencyAmplitude(), None, Detuning()):
                duration = self.rabi_frequency_amplitude.global_.times[-1]
                self.rabi_frequency_phase = RabiFrequencyPhase(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )

            case (None, RabiFrequencyPhase(), Detuning()):
                duration = self.rabi_frequency_phase.global_.times[-1]
                self.rabi_frequency_amplitude = RabiFrequencyAmplitude(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )

            case (RabiFrequencyAmplitude(), None, None):
                duration = self.rabi_frequency_amplitude.global_.times[-1]
                self.detuning = Detuning(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )
                self.rabi_frequency_phase = RabiFrequencyPhase(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )

            case (None, RabiFrequencyPhase(), None):
                duration = self.rabi_frequency_phase.global_.times[-1]
                self.rabi_frequency_amplitude = RabiFrequencyAmplitude(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )
                self.detuning = Detuning(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )

            case (None, None, Detuning()):
                duration = self.detuning.global_.times[-1]
                self.rabi_frequency_amplitude = RabiFrequencyAmplitude(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )
                self.rabi_frequency_phase = RabiFrequencyPhase(
                    global_=GlobalField(times=[0, duration], values=[0.0, 0.0])
                )

            case _:
                raise ValueError("No fields provided to convert to QuEra AHS program")

    def emit(self, ast: PulseExpr):
        match self.level_coupling:
            case LevelCoupling.Rydberg:
                return RydbergHamiltonian(
                    rabi_frequency_amplitude=self.rabi_frequency_amplitude,
                    rabi_frequency_phase=self.rabi_frequency_phase,
                    detuning=self.detuning,
                )
            case _:
                raise ValueError("QuEra AHS program doesn't support Hyperfine levels")
