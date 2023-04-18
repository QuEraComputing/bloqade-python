from dataclasses import dataclass
from typing import Dict
import bloqade.ir.real as real

class Scalar:
    pass

@dataclass(frozen=True)
class Literal(Scalar):
    value: real.Real

@dataclass
class Negative(Scalar):
    value: Scalar

@dataclass
class Default(Scalar):
    var: real.Real
    value: float

@dataclass
class Reduce(Scalar):
    head: str
    literal: float
    args: Dict[Scalar, int]

@dataclass
class Slice(Scalar):
    duration: Scalar
    interval: Scalar

@dataclass
class Interval(Scalar):
    start: Scalar
    stop: Scalar
