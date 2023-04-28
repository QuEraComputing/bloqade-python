from bloqade.ir.pulse import Pulse
from bloqade.ir.scalar import Interval

from pydantic.dataclasses import dataclass
from enum import Enum
from typing import List


@dataclass(frozen=True)
class LevelCoupling(str, Enum):
    Rydberg = "rydberg"
    Hyperfine = "hyperfine"

@dataclass(frozen=True)
class Sequence:
    pass

@dataclass(frozen=True)
class Append(Sequence):
    value: List[Sequence]



@dataclass(frozen=True)
class Instruction(Sequence):
    value: dict[LevelCoupling, Pulse]

    def __call__(
        self, 
        clock_s: float, 
        level_coupling: LevelCoupling,
        *args, 
        **kwargs
    ):
        return self.value[level_coupling](clock_s, *args, **kwargs)


@dataclass(frozen=True)
class NamedSequence(Sequence):
    sequence: Sequence
    name: str

@dataclass(frozen=True)
class Slice(Sequence):
    sequence: Sequence
    interval: Interval
