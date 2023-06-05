from pydantic.dataclasses import dataclass
from .scalar import Scalar, cast, Literal
from .waveform import Waveform
from typing import Dict, Optional, Tuple, Union
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
        return "Uniform"

    def print_node(self):
        return "UniformModulation"

    def children(self):
        return []

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


Uniform = UniformModulation()


@dataclass(frozen=True)
class RabiScale:
    """
    <rabi_scale> ::= `rabi_scale(` <scalar> `,` <scalar> `)`
    """

    amplitude_scale: Scalar
    phase_shift: Scalar = Literal(0.0)

    def print_node(self):
        return "RabiScale"

    def children(self):
        return {
            "amplitude_scale": self.amplitude_scale,
            "phase_shift": self.phase_shift,
        }

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False)
class ScaledLocations(SpatialModulation):
    value: dict[Location, Union[Scalar, RabiScale]]

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
        # should return dict consisting of Location and scale
        annotated_children = {}
        for loc, scale in self.value.items():
            annotated_children[loc.print_node()] = scale

        return annotated_children

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


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


@dataclass
class Field:
    """
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    """

    value: Dict[SpatialModulation, Waveform]

    def __hash__(self) -> int:
        return hash(frozenset(self.value.items())) ^ hash(self.__class__)

    def __repr__(self) -> str:
        return f"Field({self.value!r})"

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

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class RabiWaveform:
    """
    <rabi_waveform> ::= `rabi_waveform(` <waveform> `,` <waveform> `)`
    """

    amplitude: Waveform
    phase: Optional[Waveform]

    def print_node(self):
        return "RabiWaveform"

    def children(self):
        return {"amplitude": self.amplitude, "phase": self.phase}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class RabiField:
    """
    <rabi field> ::= ('rabi_field' <spatial modulation>  <rabi_waveform>)*

    """

    # can't use Dict because RabiWaveform doesn't support __add__
    value: Tuple[Tuple[SpatialModulation, RabiWaveform]]

    def __repr__(self) -> str:
        return f"RabiField({self.value!r})"

    def add(self, other):
        if not isinstance(other, RabiField):
            raise ValueError(f"Cannot add RabiField and {other.__class__}")

        return RabiField(self.value + other.value)

    def print_node(self):
        return "RabiField"

    def children(self):
        # return dict with annotations
        return {repr(spatial_mod): wf for spatial_mod, wf in self.value}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)
