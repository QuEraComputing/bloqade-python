from pydantic.dataclasses import dataclass
from .scalar import Scalar
from .waveform import Waveform


@dataclass
class Location:
    value: int


@dataclass
class SpatialModulation:
    pass


@dataclass
class Global(SpatialModulation):
    pass


@dataclass
class RunTimeVector(SpatialModulation):
    name: str


@dataclass
class ScaledLocations(SpatialModulation):
    value: dict[Location, Scalar]


@dataclass
class Field:
    """
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    """

    value: dict[SpatialModulation, Waveform]
