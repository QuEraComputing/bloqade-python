from pydantic.dataclasses import dataclass
from typing import Any, Union, List, Tuple
from enum import Enum
from bloqade.ir.scalar import Scalar, Interval
from bloqade.hardware.to_quera import TimeSeriesType


@dataclass(frozen=True)
class Waveform:
    """
    <waveform> ::= <instruction>
        | <smooth>
        | <slice>
        | <append>
        | <negative>
        | <scale>
        | <add>
    """

    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError
    
    def add(self, other: "Waveform") -> "Waveform":
        return self.canonicalize(Add(self, other))
    
    def align(self, waveform: "Waveform", alignment: str) -> "Waveform":
        return self.canonicalize(AlignedWaveform(waveform, alignment, AlignedValue.Left))

    @staticmethod
    def canonicalize(expr: "Waveform") -> "Waveform":
        return expr


class AlignedValue(str, Enum):
    Left = "left_value"
    Right = "right_value"


@dataclass(frozen=True)
class AlignedWaveform(Waveform):
    """
    <padded waveform> ::= <waveform> | <waveform> <alignment> <value>

    <alignment> ::= 'left aligned' | 'right aligned'
    <value> ::= 'left value' | 'right value' | <scalar expr>
    """

    waveform: Waveform
    alignment: str
    value: Union[Scalar, AlignedValue]


@dataclass(frozen=True)
class Instruction(Waveform):
    duration: Scalar

@dataclass(frozen=True)
class Linear(Instruction):
    """
    <linear> ::= 'linear' <scalar expr> <scalar expr>
    """

    start: Scalar
    stop: Scalar

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Constant(Instruction):
    """
    <constant> ::= 'constant' <scalar expr> <scalar expr>
    """

    value: Scalar

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Poly(Instruction):
    """
    <poly> ::= <scalar>+
    """

    checkpoints: List[Scalar]

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Smooth(Waveform):
    """
    <smooth> ::= 'smooth' <kernel> <waveform>
    """

    kernel: str
    waveform: Waveform

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Slice(Waveform):
    """
    <slice> ::= <waveform> <scalar.interval>
    """

    waveform: Waveform
    interval: Interval

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Append(Waveform):
    """
    <append> ::= <waveform> | <append> <waveform>
    """

    waveforms: List[Waveform]

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Negative(Waveform):
    """
    <negative> ::= '-' <waveform>
    """

    waveform: Waveform

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        return -self.waveform(clock_s, **kwargs)


@dataclass(frozen=True)
class Scale(Waveform):
    """
    <scale> ::= <scalar expr> '*' <waveform>
    """

    scalar: Scalar
    waveform: Waveform

    def __call__(self, clock_s: float, **kwargs) -> Any:
        return self.scalar(**kwargs) * self.waveform(clock_s, **kwargs)


@dataclass(frozen=True)
class Add(Waveform):
    """
    <add> ::= <waveform> '+' <waveform>
    """

    left: Waveform
    right: Waveform

    def __call__(self, clock_s: float, **kwargs) -> Any:
        return self.left(clock_s, **kwargs) + self.right(clock_s, **kwargs)
