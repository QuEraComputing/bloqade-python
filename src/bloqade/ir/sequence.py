from bloqade.ir.pulse import Pulse
from bloqade.ir.scalar import Interval

from pydantic.dataclasses import dataclass
from enum import Enum
from typing import List


@dataclass(frozen=True)
class LevelCoupling:
    pass


@dataclass(frozen=True)
class Rydberg(LevelCoupling):
    pass


@dataclass(frozen=True)
class Hyperfine(LevelCoupling):
    pass


@dataclass(frozen=True)
class Sequence:
    pass


@dataclass(frozen=True)
class Append(Sequence):
    value: List[Sequence]


@dataclass(frozen=True)
class Instruction(Sequence):
    value: dict[LevelCoupling, Pulse]


@dataclass(frozen=True)
class NamedSequence(Sequence):
    sequence: Sequence
    name: str


@dataclass(frozen=True)
class Slice(Sequence):
    sequence: Sequence
    interval: Interval
