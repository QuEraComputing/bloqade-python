from dataclasses import fields
from functools import cached_property
from .pulse import PulseExpr, Pulse
from ..scalar import Interval, Scalar, cast
from ..tree_print import Printer

from pydantic.dataclasses import dataclass
from beartype.typing import List, Dict
from bloqade.visualization import get_ir_figure
from bloqade.visualization import display_ir


__all__ = [
    "LevelCoupling",
    "rydberg",
    "hyperfine",
    "Sequence",
    "NamedSequence",
]


@dataclass(frozen=True)
class LevelCoupling:
    def children(self):
        return []

    def __str__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __eq__(self, other):
        return self.__class__ == other.__class__


@dataclass(frozen=True)
class RydbergLevelCoupling(LevelCoupling):
    def print_node(self):
        return "RydbergLevelCoupling"


@dataclass(frozen=True)
class HyperfineLevelCoupling(LevelCoupling):
    def print_node(self):
        return "HyperfineLevelCoupling"


rydberg = RydbergLevelCoupling()
hyperfine = HyperfineLevelCoupling()


@dataclass(frozen=True)
class SequenceExpr:
    def append(self, other: "SequenceExpr") -> "SequenceExpr":
        return SequenceExpr.canonicalize(Append([self, other]))

    def set_name(self, name: str):  # no need to call canonicalize here
        return NamedSequence(self, name)

    def __getitem__(self, s: slice) -> "Slice":
        return self.canonicalize(Slice(self, Interval.from_slice(s)))

    @staticmethod
    def canonicalize(expr: "SequenceExpr") -> "SequenceExpr":
        return expr

    def __str__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def _get_data(self, **assignment):
        raise NotImplementedError

    def figure(self, **assignment):
        raise NotImplementedError

    def show(self, **assignment):
        raise NotImplementedError

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
class Append(SequenceExpr):
    sequences: List[SequenceExpr]

    __hash__ = SequenceExpr.__hash__

    @cached_property
    def duration(self) -> Scalar:
        duration = cast(0)
        for p in self.sequences:
            duration = duration + p.duration

        return duration

    def children(self):
        return self.sequences

    def print_node(self):
        return "Append"


@dataclass(frozen=True)
class Sequence(SequenceExpr):
    """Sequence of a program, which includes pulses informations."""

    pulses: dict[LevelCoupling, PulseExpr]

    __hash__ = SequenceExpr.__hash__

    @staticmethod
    def create(pulses: Dict = {}) -> "Sequence":
        processed_pulses = {}
        for level_coupling, pulse in pulses.items():
            if not isinstance(level_coupling, LevelCoupling):
                raise TypeError(f"Unexpected type {type(level_coupling)}")

            if isinstance(pulse, PulseExpr):
                processed_pulses[level_coupling] = pulse
            elif isinstance(pulse, dict):
                processed_pulses[level_coupling] = Pulse.create(pulse)
            else:
                raise TypeError(f"Unexpected type {type(pulse)}")
        return Sequence(processed_pulses)

    @cached_property
    def duration(self) -> Scalar:
        # Pulses are all aligned so that they all start at 0.
        duration = cast(0)
        for p in self.pulses.values():
            duration = duration.max(p.duration)

        return duration

    def __call__(self, clock_s: float, level_coupling: LevelCoupling, *args, **kwargs):
        return self.pulses[level_coupling](clock_s, *args, **kwargs)

    # return annotated version
    def children(self):
        return {k.print_node(): v for k, v in self.pulses.items()}

    def print_node(self):
        return "Sequence"

    def _get_data(self, **assignments):
        return None, self.pulses

    def figure(self, **assignments):
        return get_ir_figure(self, **assignments)

    def show(self, **assignments):
        """
        Interactive visualization of the Sequence

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the Sequence

        """
        display_ir(self, assignments)


@dataclass(frozen=True)
class NamedSequence(SequenceExpr):
    name: str
    sequence: SequenceExpr

    __hash__ = SequenceExpr.__hash__

    @cached_property
    def duration(self) -> Scalar:
        return self.sequence.duration

    def children(self):
        return {"sequence": self.sequence, "name": self.name}

    def print_node(self):
        return "NamedSequence"

    def _get_data(self, **assignment):
        return self.name, self.sequence.value

    def figure(self, **assignments):
        return get_ir_figure(self, **assignments)

    def show(self, **assignments):
        display_ir(self, assignments)


@dataclass(frozen=True)
class Slice(SequenceExpr):
    sequence: SequenceExpr
    interval: Interval

    __hash__ = SequenceExpr.__hash__

    @cached_property
    def duration(self) -> Scalar:
        return self.sequence.duration[self.interval.start : self.interval.stop]

    def children(self):
        return {"sequence": self.sequence, "interval": self.interval}

    def print_node(self):
        return "Slice"
