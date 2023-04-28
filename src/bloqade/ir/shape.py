from pydantic.dataclasses import dataclass
from typing import List

from bloqade.ir.scalar import Scalar
from bloqade.julia.prelude import *


@dataclass(frozen=True)
class Shape(ToJulia):
    """
    <shape> ::= <linear shape>
      | <constant shape>
      | <poly>
    """

    pass


@dataclass(frozen=True)
class Linear(Shape):
    """
    <linear shape> ::= 'linear' <scalar expr> <scalar expr>
    """

    start: Scalar
    stop: Scalar

    def julia(self):
        return IRTypes.Linear(self.start.julia(), self.stop.julia())


@dataclass(frozen=True)
class Constant(Shape):
    """
    <constant shape> ::= 'constant' <scalar expr>
    """

    value: Scalar

    def julia(self):
        return IRTypes.Constant(self.value.julia())


@dataclass(frozen=True)
class Poly(Shape):
    """
    <poly> ::= <scalar expr> | <poly> <scalar expr>
    """

    checkpoints: List[Scalar]

    def julia(self):
        return IRTypes.Poly(Vector[IRTypes.ScalarLang](self.checkpoints))
