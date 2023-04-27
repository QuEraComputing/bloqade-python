from pydantic.dataclasses import dataclass
from .scalar import Scalar
from .waveform import Waveform
from ..julia.prelude import *
from enum import Enum


class FieldName(str, Enum, ToJulia):
    RabiFrequencyAmplitude = "rabi_frequency_amplitude"
    RabiFrequencyPhase = "rabi_frequency_phase"
    Detuning = "detuning"


@dataclass(frozen=True)
class Location(ToJulia):
    value: int

    def julia(self) -> AnyValue:
        return Int64(self.value)

@dataclass(frozen=True)
class SpatialModulation(ToJulia):
    pass


@dataclass(frozen=True)
class Global(SpatialModulation):
    
    def julia(self) -> AnyValue:
        return IRTypes.Global


@dataclass(frozen=True)
class RunTimeVector(SpatialModulation):
    name: str

    def julia(self) -> AnyValue:
        return IRTypes.RuntimeVector(Symbol(self.name))

@dataclass(frozen=True)
class ScaledLocations(SpatialModulation):
    value: dict[Location, Scalar]

    def julia(self) -> AnyValue:
        return IRTypes.ScaledLocations(
            Dict[IRTypes.Location, IRTypes.ScalarLang](self.value)
        )

@dataclass(frozen=True)
class Field(ToJulia):
    """
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    """

    value: dict[SpatialModulation, Waveform]

    def julia(self) -> AnyValue:
        return IRTypes.FieldLang.Field(
            Dict[IRTypes.SpatialModulation, IRTypes.WaveformLang](self.value)
        )
