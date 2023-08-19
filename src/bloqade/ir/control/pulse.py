from ..scalar import Interval
from .field import Field
from typing import List
from pydantic.dataclasses import dataclass
from ..tree_print import Printer
from bokeh.io import show
from bloqade.visualization.ir_visualize import get_pulse_figure

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

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class RabiFrequencyAmplitude(FieldName):
    def __str__(self):
        return "rabi_frequency_amplitude"

    def print_node(self):
        return "RabiFrequencyAmplitude"


@dataclass(frozen=True)
class RabiFrequencyPhase(FieldName):
    def __str__(self):
        return "rabi_frequency_phase"

    def print_node(self):
        return "RabiFrequencyPhase"


@dataclass(frozen=True)
class Detuning(FieldName):
    def __str__(self):
        return "detuning"

    def print_node(self):
        return "Detuning"


class RabiRouter:
    def __init__(self) -> None:
        self.amplitude = RabiFrequencyAmplitude()
        self.phase = RabiFrequencyPhase()

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        return "rabi (amplitude, phase)"

    def print_node(self):
        return "RabiRouter"

    def children(self):
        return {"Amplitude": self.amplitude, "Phase": self.phase}


rabi = RabiRouter()
detuning = Detuning()


@dataclass
class PulseExpr:
    """
    ```bnf
    <expr> ::= <pulse>
      | <append>
      | <slice>
      | <named>
    ```
    """

    def append(self, other: "PulseExpr") -> "PulseExpr":
        return PulseExpr.canonicalize(Append([self, other]))

    def slice(self, interval: Interval) -> "PulseExpr":
        return PulseExpr.canonicalize(Slice(self, interval))

    @staticmethod
    def canonicalize(expr: "PulseExpr") -> "PulseExpr":
        # TODO: update canonicalization rules for appending pulses
        match expr:
            case Append([Append(lhs), Append(rhs)]):
                return Append(list(map(PulseExpr.canonicalize, lhs + rhs)))
            case Append([Append(pulses), pulse]):
                return PulseExpr.canonicalize(Append(pulses + [pulse]))
            case Append([pulse, Append(pulses)]):
                return PulseExpr.canonicalize(Append([pulse] + pulses))
            case _:
                return expr
        return expr

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def _get_data(self, **assigments):
        return NotImplementedError

    def figure(self, **assignments):
        return NotImplementedError

    def show(self, **assignments):
        return NotImplementedError


@dataclass
class Append(PulseExpr):
    """
    ```bnf
    <append> ::= <expr>+
    ```
    """

    value: List[PulseExpr]

    def __str__(self):
        return "pulse.Append(value=" + f"{str([v.print_node() for v in self.value])})"

    def print_node(self):
        return "Append"

    def children(self):
        return self.value


@dataclass(init=False, repr=False)
class Pulse(PulseExpr):
    """
    ```bnf
    <pulse> ::= (<field name> <field>)+
    ```
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

    def __str__(self):
        return f"Pulse(value={str(self.value)})"

    def print_node(self):
        return "Pulse"

    def children(self):
        # annotated children
        annotated_children = {
            field_name.print_node(): field for field_name, field in self.value.items()
        }
        return annotated_children

    def _get_data(self, **assigments):
        return None, self.value

    def figure(self, **assignments):
        return get_pulse_figure(self, **assignments)

    def show(self, **assignments):
        show(self.figure(**assignments))


@dataclass
class NamedPulse(PulseExpr):
    name: str
    pulse: PulseExpr

    def __str__(self):
        return f"NamedPulse(name={str(self.name)})"

    def print_node(self):
        return "NamedPulse"

    def children(self):
        return {"Name": self.name, "Pulse": self.pulse}

    def _get_data(self, **assigments):
        return self.name, self.pulse.value

    def figure(self, **assignments):
        return get_pulse_figure(self, **assignments)

    def show(self, **assignments):
        show(self.figure(**assignments))


@dataclass
class Slice(PulseExpr):
    pulse: PulseExpr
    interval: Interval

    def __str__(self):
        return f"{self.pulse.print_node()}[{str(self.interval)}]"

    def print_node(self):
        return "Slice"

    def children(self):
        return {"Pulse": self.pulse, "Interval": self.interval}
