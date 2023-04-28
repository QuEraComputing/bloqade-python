from bloqade.julia.prelude import *
from bloqade.ir.pulse import Pulse
from bloqade.ir.scalar import Interval

from pydantic.dataclasses import dataclass
from enum import Enum
from typing import List
from ..julia.prelude import *
from juliacall import AnyValue  # type: ignore


@dataclass(frozen=True)
class LevelCoupling(ToJulia):
    pass


@dataclass(frozen=True)
class Rydberg(LevelCoupling):
    def julia(self):
        return IRTypes.Rydberg


@dataclass(frozen=True)
class Hyperfine(LevelCoupling):
    def julia(self):
        return IRTypes.Hyperfine


@dataclass(frozen=True)
class Sequence(ToJulia):
    pass


@dataclass(frozen=True)
class Append(Sequence):
    value: List[Sequence]

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Append(Vector[IRTypes.SequenceLang](self.value))


@dataclass(frozen=True)
class Instruction(Sequence):
    value: dict[LevelCoupling, Pulse]

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Instruction(
            Dict[IRTypes.LevelCoupling, IRTypes.PulseLang](self.value)
        )


@dataclass(frozen=True)
class NamedSequence(Sequence):
    sequence: Sequence
    name: str

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Name(
            self.sequence.julia(),
            IRTypes.String(self.name),
        )


@dataclass(frozen=True)
class Slice(Sequence):
    sequence: Sequence
    interval: Interval

    def julia(self) -> AnyValue:
        return IRTypes.SequenceLang.Slice(
            self.sequence.julia(),
            self.interval.julia(),
        )
