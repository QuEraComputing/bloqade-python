from bloqade.ir.pulse import Pulse
from bloqade.ir.scalar import Interval

from pydantic.dataclasses import dataclass
from enum import Enum
from typing import List


class LevelCoupling(str, Enum):
    Rydberg = "rydberg"
    Hyperfine = "hyperfine"


@dataclass
class Sequence:
    pass


@dataclass
class Append(Sequence):
    value: List[Sequence]


@dataclass
class Instruction(Sequence):
    value: dict[LevelCoupling, Pulse]

    def __call__(self, clock_s: float, level_coupling: LevelCoupling, *args, **kwargs):
        return self.value[level_coupling](clock_s, *args, **kwargs)


@dataclass
class NamedSequence(Sequence):
    sequence: Sequence
    name: str


@dataclass
class Slice(Sequence):
    sequence: Sequence
    interval: Interval
