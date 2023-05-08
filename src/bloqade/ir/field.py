from pydantic.dataclasses import dataclass
from .scalar import Scalar, cast
from .waveform import Waveform
from .tree_print import Printer


__all__ = [
    "Field",
    "Location",
    "SpatialModulation",
    "Uniform",
    "RunTimeVector",
    "ScaledLocations",
]


@dataclass(frozen=True)
class Location:
    value: int

    def __repr__(self) -> str:
        return f"Location({self.value!r})"

    def children(self):
        return []

    def print_node(self):
        return f"Location {self.value}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


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

    def print_node(self):
        return "UniformModulation"

    def children(self):
        return []

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


Uniform = UniformModulation()


@dataclass
class RunTimeVector(SpatialModulation):
    name: str

    def __hash__(self) -> int:
        return hash(self.name) ^ hash(self.__class__)

    def __repr__(self) -> str:
        return f"RunTimeVector({self.name!r})"

    def print_node(self):
        return "RunTimeVector"

    def children(self):
        return [self.name]

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


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

    def print_node(self):
        return "ScaledLocations"

    def children(self):
        # can return list or dict
        # should return dict consisting of Location and Scalar
        annotated_children = {}
        for loc, scalar in self.value.items():
            annotated_children[loc.print_node()] = scalar

        return annotated_children

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


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

    def print_node(self):
        return "Field"

    def children(self):
        # return dict with annotations
        return {spatial_mod.print_node(): wf for spatial_mod, wf in self.value.items()}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)
