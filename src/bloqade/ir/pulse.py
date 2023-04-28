import bloqade.ir.scalar as scalar
from bloqade.ir.scalar import Interval
from bloqade.ir.field import (
    Field,
    FieldName,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
    Detuning,
)
from typing import List
from bloqade.julia.prelude import *

from pydantic.dataclasses import dataclass


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
        # TODO: update canonicalization rules for appending pulses
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
