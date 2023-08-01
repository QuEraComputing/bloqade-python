from pydantic.dataclasses import dataclass
from ..scalar import Scalar, cast
from .waveform import Waveform
from typing import Dict
from ..tree_print import Printer

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
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        return f"Location({str(self.value)})"

    def children(self):
        return []

    def print_node(self):
        return f"Location {self.value}"


@dataclass
class SpatialModulation:
    def __hash__(self) -> int:
        raise NotImplementedError

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class UniformModulation(SpatialModulation):
    def __hash__(self) -> int:
        return hash(self.__class__)

    def __str__(self):
        return "Uniform"

    def print_node(self):
        return "UniformModulation"

    def children(self):
        return []


Uniform = UniformModulation()


@dataclass
class RunTimeVector(SpatialModulation):
    name: str

    def __hash__(self) -> int:
        return hash(self.name) ^ hash(self.__class__)

    def __str__(self):
        return f"RunTimeVector({str(self.name)})"

    def print_node(self):
        return "RunTimeVector"

    def children(self):
        return [self.name]


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

    def __str__(self):
        return f"ScaledLocations(value={str(self.value)})"

    def print_node(self):
        return "ScaledLocations"

    def children(self):
        # can return list or dict
        # should return dict consisting of Location and Scalar
        annotated_children = {}
        for loc, scalar in self.value.items():
            annotated_children[loc.print_node()] = scalar

        return annotated_children


@dataclass
class Field:
    """Field node in the IR. Which contains collection(s) of
    [`Waveform`][bloqade.ir.control.waveform.Waveform]

    ```bnf
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    ```
    """

    value: Dict[SpatialModulation, Waveform]

    def __hash__(self) -> int:
        return hash(frozenset(self.value.items())) ^ hash(self.__class__)

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        return f"Field({str(self.value)})"

    def add(self, other):
        if not isinstance(other, Field):
            raise ValueError(f"Cannot add Field and {other.__class__}")

        out = Field(dict(self.value))

        for spatial_modulation, waveform in other.value.items():
            if spatial_modulation in self.value:
                out.value[spatial_modulation] = out.value[spatial_modulation] + waveform
            else:
                out.value[spatial_modulation] = waveform

        return out

    def print_node(self):
        return "Field"

    def children(self):
        # return dict with annotations
        return {spatial_mod.print_node(): wf for spatial_mod, wf in self.value.items()}
