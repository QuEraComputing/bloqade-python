import random
from pydantic.dataclasses import dataclass
from typing import List, Tuple
from .sequence import SequenceExpr
from ..task import Program

@dataclass
class Lattice:

    def run(self, seq: SequenceExpr) -> Program:
        return Program(self, seq)

@dataclass
class ListOfPosition(Lattice):
    value: List[Tuple[float, ...]]


def square(size: Tuple[int, int], filling: float=0.8):
    return ListOfPosition([(x,y) for x in range(size[0]) for y in range(size[1]) if random.random() < filling])
