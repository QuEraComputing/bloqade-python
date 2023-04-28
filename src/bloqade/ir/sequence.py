from bloqade.ir.pulse import PulseExpr, Pulse
from bloqade.ir.scalar import Interval, cast

from pydantic.dataclasses import dataclass
from enum import Enum
from typing import List, Dict


@dataclass(frozen=True, repr=False)
class LevelCoupling(str, Enum):
    Rydberg = "rydberg"
    Hyperfine = "hyperfine"

    def __repr__(self) -> str:
        return self.value

rydberg = LevelCoupling.Rydberg
hyperfine = LevelCoupling.Hyperfine

@dataclass
class SequenceExpr:
    
    def append(self, other: "SequenceExpr") -> "SequenceExpr":
        return SequenceExpr.canonicalize(Append([self, other]))
    
    def name(self, name: str): # no need to call canonicalize here
        return NamedSequence(self, name)
    
    def __getitem__(self, s: slice) -> "Slice":
        return self.canonicalize(Slice(self, Interval.from_slice(s)))

    @staticmethod
    def canonicalize(expr: "SequenceExpr") -> "SequenceExpr":
        return expr


@dataclass
class Append(SequenceExpr):
    value: List[SequenceExpr]


@dataclass(init=False, repr=False)
class Sequence(SequenceExpr):
    value: dict[LevelCoupling, PulseExpr]

    def __init__(self, seq_pairs: Dict):
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
        return 'Sequence({' + ', '.join(map(str, self.value.items())) + '})'

@dataclass
class NamedSequence(SequenceExpr):
    sequence: SequenceExpr
    name: str


@dataclass(repr=False)
class Slice(SequenceExpr):
    sequence: SequenceExpr
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.sequence!r}[{self.interval}]"
