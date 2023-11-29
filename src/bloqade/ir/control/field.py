from functools import cached_property
from ..scalar import Scalar, cast
from ..tree_print import Printer
from .waveform import Waveform
from bloqade.visualization import get_field_figure
from pydantic.dataclasses import dataclass
from beartype.typing import Dict, List, Optional
from decimal import Decimal
from bloqade.visualization import display_ir
from bloqade.visualization import get_ir_figure
from dataclasses import fields


__all__ = [
    "Field",
    "Location",
    "SpatialModulation",
    "Uniform",
    "RunTimeVector",
    "ScaledLocations",
]


class FieldExpr:
    def __str__(self):
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    @cached_property
    def _hash_value(self) -> int:
        value = hash(self.__class__)
        for field in fields(self):
            field_value = getattr(self, field.name)
            if isinstance(field_value, dict):
                value ^= hash(frozenset(field_value.items()))
            elif isinstance(field_value, list):
                value ^= hash(tuple(field_value))
            else:
                value ^= hash(field_value)

        return value

    def __hash__(self) -> int:
        return self._hash_value


@dataclass(frozen=True)
class Location(FieldExpr):
    value: int

    __hash__ = FieldExpr.__hash__

    def __str__(self):
        return f"Location({str(self.value)})"

    def children(self):
        return []

    def print_node(self):
        return f"Location({str(self.value)})"


@dataclass(frozen=True)
class SpatialModulation(FieldExpr):
    __hash__ = FieldExpr.__hash__

    def _get_data(self, **assignment):
        return {}

    def figure(self, **assignment):
        raise NotImplementedError


@dataclass(frozen=True)
class UniformModulation(SpatialModulation):
    __hash__ = SpatialModulation.__hash__

    def print_node(self):
        return "UniformModulation"

    def children(self):
        return []

    def _get_data(self, **assignment):
        return ["uni"], ["all"]

    def figure(self, **assignment):
        return get_ir_figure(self, **assignment)

    def show(self, **assignment):
        display_ir(self, **assignment)


Uniform = UniformModulation()


@dataclass(frozen=True)
class RunTimeVector(SpatialModulation):
    name: str

    __hash__ = SpatialModulation.__hash__

    def print_node(self):
        return "RunTimeVector"

    def children(self):
        return [self.name]

    def figure(self, **assginment):
        return get_ir_figure(self, **assginment)

    def _get_data(self, **assignment):
        return [self.name], ["vec"]

    def show(self, **assignment):
        display_ir(self, **assignment)


@dataclass(frozen=True)
class AssignedRunTimeVector(SpatialModulation):
    name: Optional[str]  # name is optional for literal Lists
    value: List[Decimal]

    __hash__ = SpatialModulation.__hash__

    def print_node(self):
        return "AssgiendRunTimeVector"

    def children(self):
        return [self.name, *self.value]

    def figure(self, **assginment):
        return get_ir_figure(self, **assginment)

    def _get_data(self, **assignment):
        return [self.name], ["vec"]

    def show(self, **assignment):
        display_ir(self, **assignment)


@dataclass(frozen=True)
class ScaledLocations(SpatialModulation):
    value: Dict[Location, Scalar]

    __hash__ = SpatialModulation.__hash__

    @staticmethod
    def create(value):
        processed_value = dict()
        for k, v in value.items():
            if isinstance(k, int):
                k = Location(k)
            elif isinstance(k, Location):
                pass
            else:
                raise ValueError(f"expected Location or int, got {k}")

            processed_value[k] = cast(v)

        return ScaledLocations(processed_value)

    def _get_data(self, **assignments):
        names = []
        scls = []

        for loc, scl in self.value.items():
            names.append("loc[%d]" % (loc.value))
            scls.append(str(scl(**assignments)))

        return names, scls

    def print_node(self):
        return "ScaledLocations"

    def children(self):
        # can return list or dict
        # should return dict consisting of Location and Scalar
        annotated_children = {}
        for loc, scalar in self.value.items():
            annotated_children[loc.print_node()] = scalar

        return annotated_children

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        assert isinstance(key, Location)
        self.value[key] = cast(value)

    def __bool__(self):
        return bool(self.value)

    def figure(self, **assignments):
        return get_ir_figure(self, **assignments)

    def show(self, **assignment):
        display_ir(self, assignment)


@dataclass
class Drive:
    modulation: SpatialModulation
    waveform: Waveform

    def print_node(self):
        return "Drive"

    def children(self):
        return {"modulation": self.modulation, "waveform": self.waveform}


@dataclass(frozen=True)
class Field(FieldExpr):
    """Field node in the IR. Which contains collection(s) of
    [`Waveform`][bloqade.ir.control.waveform.Waveform]

    ```bnf
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    ```
    """

    drives: Dict[SpatialModulation, Waveform]

    __hash__ = FieldExpr.__hash__

    @cached_property
    def duration(self) -> Scalar:
        # waveforms are all aligned so that they all start at 0.
        duration = cast(0)
        for val in self.drives.values():
            duration = duration.max(val.duration)

        return duration

    def canonicalize(self) -> "Field":
        """
        Canonicalize the Field by merging `ScaledLocation` nodes with the same waveform.
        """
        reversed_dirves = {}

        for sm, wf in self.drives.items():
            reversed_dirves[wf] = reversed_dirves.get(wf, []) + [sm]

        drives = {}

        for wf, sms in reversed_dirves.items():
            new_sm = [sm for sm in sms if not isinstance(sm, ScaledLocations)]
            scaled_locations_sm = [sm for sm in sms if isinstance(sm, ScaledLocations)]

            new_mask = {}

            for ele in scaled_locations_sm:
                for loc, scl in ele.value.items():
                    new_mask[loc] = new_mask.get(loc, 0) + cast(scl)

            if new_mask:
                new_sm += [ScaledLocations.create(new_mask)]

            for sm in new_sm:
                drives[sm] = wf

        return Field(drives)

    def add(self, other):
        if not isinstance(other, Field):
            raise ValueError(f"Cannot add Field and {other.__class__}")

        out = Field(dict(self.drives))

        for spatial_modulation, waveform in other.drives.items():
            if spatial_modulation in self.drives:
                out.drives[spatial_modulation] = (
                    out.drives[spatial_modulation] + waveform
                )
            else:
                out.drives[spatial_modulation] = waveform

        return out.canonicalize()

    def print_node(self):
        return "Field"

    def children(self):
        # return dict with annotations
        return [Drive(k, v) for k, v in self.drives.items()]

    def figure(self, **assignments):
        return get_field_figure(self, "Field", None, **assignments)

    def show(self, **assignments):
        """
        Interactive visualization of the Field

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the Field

        """
        display_ir(self, assignments)
