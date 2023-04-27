from pydantic.dataclasses import dataclass
from .scalar import Interval
from .field import Field, FieldName
from typing import List
from ..julia.prelude import *

@dataclass(frozen=True)
class PulseExpr:
    """
    <expr> ::= <pulse>
      | <append>
      | <slice>
      | <named>
    """

    def append(self, other: "PulseExpr") -> "PulseExpr":
        return PulseExpr.canonicalize(Append([self, other]))

    def slice(self, interval: Interval) -> "PulseExpr":
        return PulseExpr.canonicalize(Slice(self, interval))

    @staticmethod
    def canonicalize(expr: "PulseExpr") -> "PulseExpr":
        return expr


@dataclass(frozen=True)
class Append(PulseExpr):
    """
    <append> ::= <expr>+
    """

    value: List[PulseExpr]


@dataclass(frozen=True)
class Pulse(PulseExpr):
    """
    <pulse> ::= (<field name> <field>)+
    """

    value: dict[FieldName, Field]


@dataclass(frozen=True)
class NamedPulse(PulseExpr):
    name: str
    pulse: PulseExpr


@dataclass(frozen=True)
class Slice(PulseExpr):
    pulse: PulseExpr
    interval: Interval
