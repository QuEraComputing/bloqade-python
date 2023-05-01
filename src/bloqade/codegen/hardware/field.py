from pydantic.dataclasses import dataclass
from bloqade.ir.field import Field, GlobalModulation, Global
from bloqade.ir.pulse import FieldName
from typing import List, Optional
from bloqade.codegen.hardware.spatial_modulation import SpatialModulationCodeGen
from bloqade.codegen.hardware.waveform import WaveformCodeGen

from quera_ahs_utils.quera_ir.task_specification import (
    GlobalField,
    LocalField,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
    Detuning,
)


@dataclass
class FieldCodeGen(WaveformCodeGen, SpatialModulationCodeGen):
    global_: Optional[GlobalField] = None
    local: Optional[LocalField] = None

    def scan(self, ast: Field):
        waveform_codegen = WaveformCodeGen(self.n_atoms, self.variable_reference, field_name=self.field_name)
        terms = dict(ast.value)
        match self.field_name:
            case FieldName.RabiFrequencyAmplitude if len(
                terms
            ) == 1 and GlobalModulation() in terms:
                times, values = waveform_codegen.emit(terms.pop(Global))
                self.global_ = GlobalField(times=times, values=values)

            case FieldName.RabiFrequencyPhase if len(
                terms
            ) == 1 and GlobalModulation() in terms:
                times, values = waveform_codegen.emit(terms.pop(Global))
                self.global_ = GlobalField(times=times, values=values)

            case FieldName.Detuning if len(terms) == 1 and GlobalModulation() in terms:
                times, values = waveform_codegen.emit(terms.pop(Global))
                self.global_ = GlobalField(times=times, values=values)

            case FieldName.Detuning if len(terms) == 1:
                ((spatial_modulation, waveform),) = terms.items()
                times, values = waveform_codegen.emit(self, waveform)
                lattice_site_coefficients = SpatialModulationCodeGen.emit(
                    self, spatial_modulation
                )

                self.local = LocalField(
                    times=times,
                    values=values,
                    lattice_site_coefficients=lattice_site_coefficients,
                )

            case FieldName.Detuning if len(terms) == 2 and GlobalModulation() in terms:
                times, values = WaveformCodeGen.emit(terms.pop(Global))
                self.global_ = GlobalField(times=times, values=values)
                ((spatial_modulation, waveform),) = terms.items()
                times, values = WaveformCodeGen.emit(self, waveform)
                lattice_site_coefficients = SpatialModulationCodeGen.emit(
                    self, spatial_modulation
                )

                self.global_ = GlobalField(times=times, values=values)
                self.local = LocalField(
                    times=times,
                    values=values,
                    lattice_site_coefficients=lattice_site_coefficients,
                )

            case _:  # TODO: improve error message here
                raise NotImplementedError

    def emit(self, ast: Field):
        self.global_ = None
        self.local = None
        self.scan(ast)

        match self.field_name:
            case FieldName.RabiFrequencyAmplitude:
                return RabiFrequencyAmplitude(global_=self.global_)
            case FieldName.RabiFrequencyPhase:
                return RabiFrequencyPhase(global_=self.global_)
            case FieldName.Detuning:
                return Detuning(global_=self.global_, local=self.local)
