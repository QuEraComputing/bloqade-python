from dataclasses import dataclass
from typing import Dict
import bloqade.ir.real as real

class Scalar:
    pass


@dataclass(frozen=True)
class Literal(Scalar):
    value: real.Real

@dataclass(frozen=True)
class Negative(Scalar):
    value: Scalar

@dataclass(frozen=True)
class Default(Scalar):
    var: real.Real
    value: float

@dataclass(frozen=True)
class Reduce(Scalar):
    head: str
    literal: float
    args: Dict[Scalar, int]

@dataclass(frozen=True)
class Slice(Scalar):
    duration: Scalar
    interval: Scalar

@dataclass(frozen=True)
class Interval(Scalar):
    start: Scalar
    stop: Scalar
