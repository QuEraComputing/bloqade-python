from .pulse import PulseExpr, Pulse
from ..scalar import Interval
from ..tree_print import Printer

from pydantic.dataclasses import dataclass
from typing import List, Dict
from bloqade.visualization.ir_visualize import get_sequence_figure
from bloqade.visualization.display import display_sequence


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

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    pass


@dataclass(frozen=True)
class RydbergLevelCoupling(LevelCoupling):
    def __str__(self):
        return "rydberg"

    def print_node(self):
        return "RydbergLevelCoupling"


@dataclass(frozen=True)
class HyperfineLevelCoupling(LevelCoupling):
    def __str__(self):
        return "hyperfine"

    def print_node(self):
        return "HyperfineLevelCoupling"


rydberg = RydbergLevelCoupling()
hyperfine = HyperfineLevelCoupling()


@dataclass
class SequenceExpr:
    def append(self, other: "SequenceExpr") -> "SequenceExpr":
        return SequenceExpr.canonicalize(Append([self, other]))

    def name(self, name: str):  # no need to call canonicalize here
        return NamedSequence(self, name)

    def __getitem__(self, s: slice) -> "Slice":
        return self.canonicalize(Slice(self, Interval.from_slice(s)))

    @staticmethod
    def canonicalize(expr: "SequenceExpr") -> "SequenceExpr":
        return expr

    def __repr__(self) -> str:
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


@dataclass
class Append(SequenceExpr):
    value: List[SequenceExpr]

    def __str__(self):
        return f"sequence.Append(value={str(self.value)})"

    def children(self):
        return self.value

    def print_node(self):
        return "Append"


@dataclass(init=False, repr=False)
class Sequence(SequenceExpr):
    """Sequence of a program, which includes pulses informations."""

    pulses: dict[LevelCoupling, PulseExpr]

    def __init__(self, seq_pairs: Dict | None = None):
        if seq_pairs is None:
            self.pulses = {}
            return

        pulses = {}
        for level_coupling, pulse in seq_pairs.items():
            if not isinstance(level_coupling, LevelCoupling):
                raise TypeError(f"Unexpected type {type(level_coupling)}")

            if isinstance(pulse, PulseExpr):
                pulses[level_coupling] = pulse
            elif isinstance(pulse, dict):
                pulses[level_coupling] = Pulse(pulse)
            else:
                raise TypeError(f"Unexpected type {type(pulse)}")
        self.pulses = pulses

    def __call__(self, clock_s: float, level_coupling: LevelCoupling, *args, **kwargs):
        return self.pulses[level_coupling](clock_s, *args, **kwargs)

    def __str__(self):
        return f"Sequence({str(self.pulses)})"

    # return annotated version
    def children(self):
        return {
            level_coupling.print_node(): pulse_expr
            for level_coupling, pulse_expr in self.pulses.items()
        }

    def print_node(self):
        return "Sequence"

    def _get_data(self, **assignments):
        return None, self.pulses

    def figure(self, **assignments):
        return get_sequence_figure(self, **assignments)

    def show(self, **assignments):
        """
        Interactive visualization of the Sequence

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the Sequence

        """
        display_sequence(self, assignments)


@dataclass
class NamedSequence(SequenceExpr):
    sequence: SequenceExpr
    name: str

    def __str__(self):
        return f"NamedSequence(sequence, name='{str(self.name)}')"

    def children(self):
        return {"sequence": self.sequence, "name": self.name}

    def print_node(self):
        return "NamedSequence"

    def _get_data(self, **assignment):
        return self.name, self.sequence.value

    def figure(self, **assignments):
        return get_sequence_figure(self, **assignments)

    def show(self, **assignments):
        display_sequence(self, assignments)


@dataclass(repr=False)
class Slice(SequenceExpr):
    sequence: SequenceExpr
    interval: Interval

    def __str__(self):
        return f"Sequence[{str(self.interval)}]"

    def children(self):
        return {"sequence": self.sequence, "interval": self.interval}

    def print_node(self):
        return "Slice"
