from .scalar import Interval
from .field import Field
from typing import List
from enum import Enum
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class FieldName:
    pass

@dataclass(frozen=True)
class RabiFrequencyAmplitude(FieldName):
    def __repr__(self) -> str:
        return "rabi_frequency_amplitude"

@dataclass(frozen=True)
class RabiFrequencyPhase(FieldName):
    
    def __repr__(self) -> str:
        return "rabi_frequency_phase"

@dataclass(frozen=True)
class Detuning(FieldName):
    
    def __repr__(self) -> str:
        return "detuning"

class RabiRouter:
    def __init__(self) -> None:
        self.amplitude = RabiFrequencyAmplitude()
        self.phase = RabiFrequencyPhase()

    def __repr__(self) -> str:
        "rabi (amplitude, phase)"


rabi = RabiRouter()
detuning = Detuning()

@dataclass
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
        # TODO: update canonicalization rules for appending pulses
        return expr


@dataclass
class Append(PulseExpr):
    """
    <append> ::= <expr>+
    """

    value: List[PulseExpr]


@dataclass(init=False, repr=False)
class Pulse(PulseExpr):
    """
    <pulse> ::= (<field name> <field>)+
    """

    value: dict[FieldName, Field]

    def __init__(self, field_pairs):
        value = dict()
        for k, v in field_pairs.items():
            if isinstance(v, Field):
                value[k] = v
            elif isinstance(v, dict):
                value[k] = Field(v)
            else:
                raise TypeError(f"Expected Field or dict, got {type(v)}")
        self.value = value

    def __repr__(self) -> str:
        return "Pulse({" + ", ".join(map(str, self.value.items())) + "})"


@dataclass
class NamedPulse(PulseExpr):
    name: str
    pulse: PulseExpr


@dataclass
class Slice(PulseExpr):
    pulse: PulseExpr
    interval: Interval
