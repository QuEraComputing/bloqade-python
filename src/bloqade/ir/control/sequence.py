from collections import OrderedDict
from functools import cached_property
from bloqade.ir.control.pulse import PulseExpr, Pulse
from bloqade.ir.control.traits import (
    HashTrait,
    AppendTrait,
    SliceTrait,
    CanonicalizeTrait,
)
from bloqade.ir.scalar import Interval, Scalar, cast
from bloqade.ir.tree_print import Printer

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

    def __str__(self):
        return "Rydberg"


@dataclass(frozen=True)
class HyperfineLevelCoupling(LevelCoupling):
    def print_node(self):
        return "HyperfineLevelCoupling"

    def __str__(self):
        return "Hyperfine"


rydberg = RydbergLevelCoupling()
hyperfine = HyperfineLevelCoupling()


@dataclass(frozen=True)
class SequenceExpr(HashTrait, CanonicalizeTrait):
    __hash__ = HashTrait.__hash__

    def append(self, other: "SequenceExpr") -> "SequenceExpr":
        return SequenceExpr.canonicalize(Append([self, other]))

    def set_name(self, name: str):  # no need to call canonicalize here
        return NamedSequence(self, name)

    def __getitem__(self, s: slice) -> "Slice":
        return self.canonicalize(Slice(self, Interval.from_slice(s)))

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


@dataclass(frozen=True)
class Append(AppendTrait, SequenceExpr):
    sequences: List[SequenceExpr]

    __hash__ = SequenceExpr.__hash__

    @property
    def _sub_exprs(self):
        return self.sequences

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
        if len(self.pulses) == 0:
            return cast(0)

        pulses = list(self.pulses.values())
        duration = pulses[0].duration
        for p in pulses[1:]:
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
        return OrderedDict([("name", self.name), ("sequence", self.sequence)])

    def print_node(self):
        return "NamedSequence"

    def _get_data(self, **assignment):
        return self.name, self.sequence.value

    def figure(self, **assignments):
        return get_ir_figure(self, **assignments)

    def show(self, **assignments):
        display_ir(self, assignments)


@dataclass(frozen=True)
class Slice(SliceTrait, SequenceExpr):
    sequence: SequenceExpr
    interval: Interval

    __hash__ = SequenceExpr.__hash__

    @property
    def _sub_expr(self):
        return self.sequence

    def children(self):
        return [self.interval, self.sequence]

    def print_node(self):
        return "Slice"
