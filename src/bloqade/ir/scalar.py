from dataclasses import dataclass
from typing import Dict
import bloqade.ir.real as real


class ScalarLang:
    def __add__(self, other):
        if not isinstance(other, ScalarLang):
            raise ValueError("Cannot add non-ScalarLang objects.")
        
        match (self, other):
            case (
                    Scalar(value=real.Literal(value=lhs)), 
                    Scalar(value=real.Literal(value=rhs))
                ):
                return Scalar(value=real.Literal(value=(lhs+rhs)))
            case _:
                return Reduce(
                    head="+", 
                    literal=0, 
                    args={self:1, other:1}
                )
                
    def __neg__(self):
        match self:
            case Negative(value=value):
                return value
            case _:
                return Negative(self)


@dataclass(frozen=True)
class Scalar(ScalarLang):
    value: real.Real

@dataclass(frozen=True)
class Negative(ScalarLang):
    value: ScalarLang


@dataclass(frozen=True)
class Default(ScalarLang):
    var: real.Real
    value: float


@dataclass(frozen=True)
class Reduce(ScalarLang):
    head: str
    literal: float
    args: Dict[ScalarLang, int]


@dataclass(frozen=True)
class Slice(ScalarLang):
    duration: ScalarLang
    interval: ScalarLang


@dataclass(frozen=True)
class Interval(ScalarLang):
    start: ScalarLang
    stop: ScalarLang
