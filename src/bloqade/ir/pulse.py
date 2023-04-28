import bloqade.ir.scalar as scalar
from bloqade.ir.scalar import Interval
from bloqade.ir.field import Field
from typing import List
from enum import Enum
from pydantic.dataclasses import dataclass


@dataclass
class FieldName(str, Enum):
    RabiFrequencyAmplitude = "rabi_frequency_amplitude"
    RabiFrequencyPhase = "rabi_frequency_phase"
    Detuning = "detuning"


@dataclass
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


@dataclass
class Append(Pulse):
    """
    <append> ::= <expr>+
    """

    value: List[Pulse]


@dataclass
class Instruction(Pulse):
    """
    <pulse> ::= (<field name> <field>)+
    """

    value: dict[FieldName, Field]


@dataclass
class NamedPulse(Pulse):
    name: str
    pulse: Pulse


@dataclass
class Slice(Pulse):
    pulse: Pulse
    interval: Interval
