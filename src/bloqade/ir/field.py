from pydantic.dataclasses import dataclass
from .scalar import Scalar
from .waveform import Waveform


@dataclass(frozen=True)
class FieldName:
    pass


class RabiFrequencyAmplitude(FieldName):
    pass


class RabiFrequencyPhase(FieldName):
    pass


class Detuning(FieldName):
    pass


@dataclass(frozen=True)
class Location:
    value: int


@dataclass(frozen=True)
class SpatialModulation:
    pass


@dataclass(frozen=True)
class Global(SpatialModulation):
    pass


@dataclass(frozen=True)
class RunTimeVector(SpatialModulation):
    name: str


@dataclass(frozen=True)
class ScaledLocations(SpatialModulation):
    value: dict[Location, Scalar]


@dataclass(frozen=True)
class Field:
    """
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    """

    value: dict[SpatialModulation, Waveform]
