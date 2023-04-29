from pydantic.dataclasses import dataclass
from .scalar import Scalar, cast
from .waveform import Waveform


@dataclass(frozen=True)
class Location:
    value: int


@dataclass
class SpatialModulation:
    def __hash__(self) -> int:
        raise NotImplementedError


@dataclass
class GlobalModulation(SpatialModulation):
    def __hash__(self) -> int:
        return hash(self.__class__)

    def __repr__(self) -> str:
        return "Global"


Global = GlobalModulation()


@dataclass
class RunTimeVector(SpatialModulation):
    name: str

    def __hash__(self) -> int:
        return hash(self.name) ^ hash(self.__class__)


@dataclass(init=False)
class ScaledLocations(SpatialModulation):
    value: dict[Location, Scalar]

    def __init__(self, pairs):
        value = dict()
        for k, v in pairs.items():
            if isinstance(k, int):
                k = Location(k)
            elif isinstance(k, Location):
                pass
            else:
                raise ValueError(f"expected Location or int, got {k}")

            value[k] = cast(v)
        self.value = value

    def __hash__(self) -> int:
        return hash(frozenset(self.value.items())) ^ hash(self.__class__)


@dataclass
class Field:
    """
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    """

    value: dict[SpatialModulation, Waveform]

    def __hash__(self) -> int:
        return hash(frozenset(self.value.items())) ^ hash(self.__class__)
