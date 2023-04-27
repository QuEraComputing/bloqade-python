from pydantic.dataclasses import dataclass
from .scalar import Interval
from .field import Field, FieldName
from typing import List
from ..julia.prelude import *

@dataclass(frozen=True)
class Pulse:
    """
    <expr> ::= <pulse>
      | <append>
      | <slice>
      | <named>
    """

    def append(self, other: "Pulse") -> "Pulse":
        return Pulse.canonicalize(Append([self, other]))

    def slice(self, interval: Interval) -> "Pulse":
        return Pulse.canonicalize(Slice(self, interval))

    @staticmethod
    def canonicalize(expr: "Pulse") -> "Pulse":
        return expr


@dataclass(frozen=True)
class Append(Pulse):
    """
    <append> ::= <expr>+
    """

    value: List[Pulse]


@dataclass(frozen=True)
class Instruction(Pulse):
    """
    <pulse> ::= (<field name> <field>)+
    """

    value: dict[FieldName, Field]
        

@dataclass(frozen=True)
class NamedPulse(Pulse):
    name: str
    pulse: Pulse


@dataclass(frozen=True)
class Slice(Pulse):
    pulse: Pulse
    interval: Interval
