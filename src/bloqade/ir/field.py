from pydantic.dataclasses import dataclass
from .scalar import Scalar, cast
from .waveform import Waveform


__all__ = [
    "Field",
    "Location",
    "SpatialModulation",
    "Global",
    "RunTimeVector",
    "ScaledLocations",
]


@dataclass(frozen=True)
class Location:
    value: int

    def __repr__(self) -> str:
        return f"Location({self.value!r})"


@dataclass
class SpatialModulation:
    def __hash__(self) -> int:
        raise NotImplementedError


@dataclass
class UniformModulation(SpatialModulation):
    def __hash__(self) -> int:
        return hash(self.__class__)

    def __repr__(self) -> str:
        return "Global"


Uniform = UniformModulation()


@dataclass
class RunTimeVector(SpatialModulation):
    name: str

    def __hash__(self) -> int:
        return hash(self.name) ^ hash(self.__class__)

    def __repr__(self) -> str:
        return f"RunTimeVector({self.name!r})"


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

    def __repr__(self) -> str:
        return f"ScaledLocations(value={self.value!r})"


@dataclass
class Field:
    """
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    """

    value: dict[SpatialModulation, Waveform]

    def __hash__(self) -> int:
        return hash(frozenset(self.value.items())) ^ hash(self.__class__)

    def __repr__(self) -> str:
        return f"Field({self.value!r})"
