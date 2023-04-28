from pydantic.dataclasses import dataclass
from src.bloqade.ir.field import RabiFrequencyPhase
from .scalar import Scalar
from .waveform import piecewise_linear, Waveform
from ..julia.prelude import *
from enum import Enum
from quera_ahs_utils.quera_ir.task_specification import GlobalField, LocalField


@dataclass(frozen=True)
class FieldName(ToJulia):
    pass


class RabiFrequencyAmplitude(FieldName):
    def julia(self) -> AnyValue:
        return IRTypes.RabiFrequencyAmplitude


class RabiFrequencyPhase(FieldName):
    def julia(self) -> AnyValue:
        return IRTypes.RabiFrequencyPhase


class Detuning(FieldName):
    def julia(self) -> AnyValue:
        return IRTypes.Detuning


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
