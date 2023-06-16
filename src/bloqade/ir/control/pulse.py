from ..scalar import Interval
from .field import Field, RabiField
from typing import List, Optional
from pydantic.dataclasses import dataclass
from ..tree_print import Printer


__all__ = [
    "Pulse",
    "NamedPulse",
    "FieldName",
    "rabi",
    "detuning",
]


@dataclass(frozen=True)
class FieldName:
    def children(self):
        return []


@dataclass(frozen=True)
class RabiFrequencyAmplitude(FieldName):
    def __repr__(self) -> str:
        return "rabi_frequency_amplitude"

    def print_node(self):
        return "RabiFrequencyAmplitude"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class RabiFrequencyPhase(FieldName):
    def __repr__(self) -> str:
        return "rabi_frequency_phase"

    def print_node(self):
        return "RabiFrequencyPhase"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Detuning(FieldName):
    def __repr__(self) -> str:
        return "detuning"

    def print_node(self):
        return "Detuning"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


class RabiRouter:
    def __init__(self) -> None:
        self.amplitude = RabiFrequencyAmplitude()
        self.phase = RabiFrequencyPhase()

    def __repr__(self) -> str:
        "rabi (amplitude, phase)"

    def print_node(self):
        return "RabiRouter"

    def children(self):
        return {"Amplitude": self.amplitude, "Phase": self.phase}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


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

    def __repr__(self) -> str:
        return f"pulse.Append(value={self.value!r})"

    def print_node(self):
        return "Append"

    def children(self):
        return self.value

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False, repr=False)
class Pulse(PulseExpr):
    """
    <pulse> ::= (<field name> <field>)+
    """

    detuning: Optional[Field]
    rabi: Optional[RabiField]

    def __init__(self, detuning: Optional[Field], rabi: Optional[RabiField]) -> None:
        if detuning is None and rabi is None:
            raise ValueError("Pulse must have at least one field")

        self.detuning = detuning
        self.rabi = rabi

    def __repr__(self) -> str:
        return f"Pulse(detuning={self.detuning!r}, rabi={self.rabi!r})"

    def print_node(self):
        return "Pulse"

    def children(self):
        # annotated children
        return {
            self.detuning.print_node(): self.detuning,
            self.rabi.print_node(): self.rabi,
        }

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class NamedPulse(PulseExpr):
    name: str
    pulse: PulseExpr

    def __repr__(self) -> str:
        return f"NamedPulse(name={self.name!r}, pulse={self.pulse!r})"

    def print_node(self):
        return "NamedPulse"

    def children(self):
        return {"Name": self.name, "Pulse": self.pulse}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class Slice(PulseExpr):
    pulse: PulseExpr
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.pulse!r}[{self.interval}]"

    def print_node(self):
        return "Slice"

    def children(self):
        return {"Pulse": self.pulse, "Interval": self.interval}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)
