from .pulse import PulseExpr, Pulse
from .scalar import Interval

from pydantic.dataclasses import dataclass
from typing import List, Dict


__all__ = [
    "LevelCoupling",
    "rydberg",
    "hyperfine",
    "Sequence",
    "NamedSequence",
]


@dataclass(frozen=True)
class LevelCoupling:
    pass


@dataclass(frozen=True)
class RydbergLevelCoupling(LevelCoupling):
    def __repr__(self) -> str:
        return "rydberg"


@dataclass(frozen=True)
class HyperfineLevelCoupling(LevelCoupling):
    def __repr__(self) -> str:
        return "hyperfine"


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


@dataclass
class Append(SequenceExpr):
    value: List[SequenceExpr]

    def __repr__(self) -> str:
        return f"sequence.Append(value={self.value!r})"


@dataclass(init=False, repr=False)
class Sequence(SequenceExpr):
    value: dict[LevelCoupling, PulseExpr]

    def __init__(self, seq_pairs: Dict | None = None):
        if seq_pairs is None:
            self.value = {}
            return

        value = {}
        for level_coupling, pulse in seq_pairs.items():
            if not isinstance(level_coupling, LevelCoupling):
                raise TypeError(f"Unexpected type {type(level_coupling)}")

            if isinstance(pulse, PulseExpr):
                value[level_coupling] = pulse
            elif isinstance(pulse, dict):
                value[level_coupling] = Pulse(pulse)
            else:
                raise TypeError(f"Unexpected type {type(pulse)}")
        self.value = value

    def __call__(self, clock_s: float, level_coupling: LevelCoupling, *args, **kwargs):
        return self.value[level_coupling](clock_s, *args, **kwargs)

    def __repr__(self) -> str:
        return f"Sequence({self.value!r})"


@dataclass
class NamedSequence(SequenceExpr):
    sequence: SequenceExpr
    name: str

    def __repr__(self) -> str:
        return f"NamedSequence(sequence={self.sequence!r}, name='{self.name!r}')"


@dataclass(repr=False)
class Slice(SequenceExpr):
    sequence: SequenceExpr
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.sequence!r}[{self.interval!r}]"
