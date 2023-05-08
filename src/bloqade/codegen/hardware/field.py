from pydantic.dataclasses import dataclass
from bloqade.ir.field import Field, UniformModulation, Uniform
from bloqade.ir.pulse import Detuning, RabiFrequencyAmplitude, RabiFrequencyPhase
from typing import Optional
from bloqade.codegen.hardware.spatial_modulation import SpatialModulationCodeGen
from bloqade.codegen.hardware.waveform import WaveformCodeGen

import quera_ahs_utils.quera_ir.task_specification as task_spec


@dataclass
class FieldCodeGen(WaveformCodeGen, SpatialModulationCodeGen):
    global_: Optional[task_spec.GlobalField] = None
    local: Optional[task_spec.LocalField] = None

    def assignment_scan(self, ast: Field):
        if self.field_name in ast.value:
            waveform_codegen = WaveformCodeGen(
                self.n_atoms, self.assignments, field_name=self.field_name
            )
            waveform_codegen.assignment_scan(ast.value[self.field_name])

    def scan(self, ast: Field):
        waveform_codegen = WaveformCodeGen(
            self.n_atoms, self.assignments, field_name=self.field_name
        )
        terms = dict(ast.value)
        match self.field_name:
            case RabiFrequencyAmplitude() if len(
                terms
            ) == 1 and UniformModulation() in terms:
                times, values = waveform_codegen.emit(terms.pop(Uniform))
                self.global_ = task_spec.GlobalField(times=times, values=values)

            case RabiFrequencyPhase() if len(
                terms
            ) == 1 and UniformModulation() in terms:
                times, values = waveform_codegen.emit(terms.pop(Uniform))
                self.global_ = task_spec.GlobalField(times=times, values=values)

            case Detuning() if len(terms) == 1 and UniformModulation() in terms:
                times, values = waveform_codegen.emit(terms.pop(Uniform))
                self.global_ = task_spec.GlobalField(times=times, values=values)

            case Detuning() if len(terms) == 1:
                ((spatial_modulation, waveform),) = terms.items()
                times, values = waveform_codegen.emit(self, waveform)
                lattice_site_coefficients = SpatialModulationCodeGen.emit(
                    self, spatial_modulation
                )

                self.local = task_spec.LocalField(
                    times=times,
                    values=values,
                    lattice_site_coefficients=lattice_site_coefficients,
                )

            case Detuning() if len(terms) == 2 and UniformModulation() in terms:
                times, values = WaveformCodeGen.emit(terms.pop(Uniform))
                self.global_ = task_spec.GlobalField(times=times, values=values)
                ((spatial_modulation, waveform),) = terms.items()
                times, values = WaveformCodeGen.emit(self, waveform)
                lattice_site_coefficients = SpatialModulationCodeGen.emit(
                    self, spatial_modulation
                )

                self.global_ = task_spec.GlobalField(times=times, values=values)
                self.local = task_spec.LocalField(
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
            case RabiFrequencyAmplitude():
                return task_spec.RabiFrequencyAmplitude(global_=self.global_)
            case RabiFrequencyPhase():
                return task_spec.RabiFrequencyPhase(global_=self.global_)
            case Detuning():
                return task_spec.Detuning(global_=self.global_, local=self.local)
            case _:
                raise RuntimeError
