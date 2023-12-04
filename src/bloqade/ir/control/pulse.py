from collections import OrderedDict
from functools import cached_property

from bloqade.ir.scalar import Interval, Scalar, cast
from bloqade.ir.tree_print import Printer
from bloqade.ir.control.field import Field
from bloqade.ir.control.traits.hash_trait import HashTrait
from beartype.typing import List
from pydantic.dataclasses import dataclass
from bloqade.visualization import get_pulse_figure
from bloqade.visualization import display_ir


__all__ = [
    "Pulse",
    "NamedPulse",
    "FieldName",
    "rabi",
    "detuning",
]


@dataclass(frozen=True)
class FieldName:
    def print_node(self):
        return self.__class__.__name__

    def children(self):
        return []

    def __str__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __eq__(self, other):
        return self.__class__ == other.__class__


@dataclass(frozen=True)
class RabiFrequencyAmplitude(FieldName):
    def print_node(self):
        return "RabiFrequencyAmplitude"


@dataclass(frozen=True)
class RabiFrequencyPhase(FieldName):
    def print_node(self):
        return "RabiFrequencyPhase"


@dataclass(frozen=True)
class Detuning(FieldName):
    def print_node(self):
        return "Detuning"


class RabiRouter:
    def __init__(self) -> None:
        self.amplitude = RabiFrequencyAmplitude()
        self.phase = RabiFrequencyPhase()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def print_node(self):
        return "RabiRouter"

    def children(self):
        return {"Amplitude": self.amplitude, "Phase": self.phase}


rabi = RabiRouter()
detuning = Detuning()


@dataclass(frozen=True)
class PulseExpr(HashTrait):
    """
    ```bnf
    <expr> ::= <pulse>
      | <append>
      | <slice>
      | <named>
    ```
    """

    __hash__ = HashTrait.__hash__

    def append(self, other: "PulseExpr") -> "PulseExpr":
        return PulseExpr.canonicalize(Append([self, other]))

    def __getitem__(self, s: slice) -> "PulseExpr":
        return PulseExpr.canonicalize(Slice(self, Interval.from_slice(s)))

    @staticmethod
    def canonicalize(expr: "PulseExpr") -> "PulseExpr":
        # TODO: update canonicalization rules for appending pulses

        if isinstance(expr, Append):
            new_pulses = []
            for pulse in expr.pulses:
                if isinstance(pulse, Append):
                    new_pulses += pulse.pulses
                else:
                    new_pulses.append(pulse)

            new_pulses = list(map(PulseExpr.canonicalize, new_pulses))
            return Append(new_pulses)
        else:
            return expr

    def __str__(self) -> str:
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


@dataclass(frozen=True)
class Append(PulseExpr):
    """
    ```bnf
    <append> ::= <expr>+
    ```
    """

    pulses: List[PulseExpr]

    __hash__ = PulseExpr.__hash__

    @cached_property
    def duration(self) -> Scalar:
        duration = cast(0)
        for p in self.pulses:
            duration = duration + p.duration

        return duration

    def print_node(self):
        return "Append"

    def children(self):
        return self.pulses


@dataclass(frozen=True)
class Pulse(PulseExpr):
    """
    ```bnf
    <pulse> ::= (<field name> <field>)+
    ```
    """

    fields: dict[FieldName, Field]

    __hash__ = PulseExpr.__hash__

    @staticmethod
    def create(fields) -> "Pulse":
        processed_fields = dict()
        for k, v in fields.items():
            if isinstance(v, Field):
                processed_fields[k] = v
            elif isinstance(v, dict):
                processed_fields[k] = Field(v)
            else:
                raise TypeError(f"Expected Field or dict, got {type(v)}")

        return Pulse(processed_fields)

    @cached_property
    def duration(self) -> Scalar:
        if len(self.fields) == 0:
            return cast(0)
        # Fields are all aligned so that they all start at 0.
        fields = list(self.fields.values())
        duration = fields[0].duration
        for val in fields[1:]:
            duration = duration.max(val.duration)

        return duration

    def print_node(self):
        return "Pulse"

    def children(self):
        # annotated children
        return {k.print_node(): v for k, v in self.fields.items()}

    def _get_data(self, **assigments):
        return None, self.fields

    def figure(self, **assignments):
        return get_pulse_figure(self, **assignments)

    def show(self, **assignments):
        """
        Interactive visualization of the Pulse

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the Pulse

        """
        display_ir(self, assignments)


@dataclass(frozen=True)
class NamedPulse(PulseExpr):
    name: str
    pulse: PulseExpr

    __hash__ = PulseExpr.__hash__

    @cached_property
    def duration(self) -> Scalar:
        return self.pulse.duration

    def print_node(self):
        return "NamedPulse"

    def children(self):
        return OrderedDict([("name", self.name), ("pulse", self.pulse)])

    def _get_data(self, **assigments):
        return self.name, self.pulse.value

    def figure(self, **assignments):
        return get_pulse_figure(self, **assignments)

    def show(self, **assignments):
        display_ir(self, assignments)


@dataclass(frozen=True)
class Slice(PulseExpr):
    pulse: PulseExpr
    interval: Interval

    __hash__ = PulseExpr.__hash__

    @cached_property
    def duration(self) -> Scalar:
        return self.pulse.duration[self.interval.start : self.interval.stop]

    def print_node(self):
        return "Slice"

    def children(self):
        return [self.interval, self.pulse]
