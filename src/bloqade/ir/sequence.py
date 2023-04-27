from pydantic.dataclasses import dataclass
from enum import Enum
from .pulse import PulseExpr
from .scalar import Interval
from typing import List
from ..julia.prelude import *
from juliacall import AnyValue # type: ignore

class LevelCoupling(str, Enum, ToJulia):
    Rydberg = "rydberg"
    Hyperfine = "hyperfine"

    def julia(self) -> AnyValue:
        if self.value == 'rydberg':
            return IRTypes.Rydberg
        elif self.value == 'hyperfine':
            return IRTypes.Hyperfine
        else:
            raise AssertionError

@dataclass(frozen=True)
class SequenceExpr(ToJulia):
    pass


@dataclass(frozen=True)
class Append(SequenceExpr):
    value: List[SequenceExpr]

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Append(
            Vector[IRTypes.SequenceLang](self.value)
        )

@dataclass(frozen=True)
class Sequence(SequenceExpr):
    value: dict[LevelCoupling, PulseExpr]

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Sequence(
            Dict[IRTypes.LevelCoupling, IRTypes.PulseLang](self.value)
        )

@dataclass(frozen=True)
class NamedSequence(SequenceExpr):
    sequence: SequenceExpr
    name: str

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Name(
            self.sequence.julia(),
            IRTypes.String(self.name),
        )


@dataclass(frozen=True)
class Slice(SequenceExpr):
    sequence: SequenceExpr
    interval: Interval

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Slice(
            self.sequence.julia(),
            self.interval.julia(),
        )
