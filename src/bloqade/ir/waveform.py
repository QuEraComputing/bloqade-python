from pydantic.dataclasses import dataclass
from typing import Union, List, Tuple
from enum import Enum
from bloqade.ir.shape import Shape
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

    def to_time_series(
        self, time_series_type: TimeSeriesType, **kwargs
    ) -> Tuple[List[float], List[float]]:
        match time_series_type:
            case TimeSeriesType.PiecewiseLinear:
                return self.piecewise_linear(**kwargs)
            case TimeSeriesType.PiecewiseConstant:
                return self.piecewise_constant(**kwargs)

    def piecewise_linear(self, **kwargs) -> Tuple[List[float], List[float]]:
        return NotImplemented

    def piecewise_constant(self, **kwargs) -> Tuple[List[float], List[float]]:
        return NotImplemented


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
    """
    <instruction> ::= <shape> <scalar expr>
    """

    shape: Shape
    duration: Scalar


@dataclass(frozen=True)
class Smooth(Waveform):
    """
    <smooth> ::= 'smooth' <kernel> <waveform>
    """

    kernel: str
    waveform: Waveform


@dataclass(frozen=True)
class Slice(Waveform):
    """
    <slice> ::= <waveform> <scalar.interval>
    """

    waveform: Waveform
    interval: Interval


@dataclass(frozen=True)
class Append(Waveform):
    """
    <append> ::= <waveform> | <append> <waveform>
    """

    waveforms: List[Waveform]


@dataclass(frozen=True)
class Negative(Waveform):
    """
    <negative> ::= '-' <waveform>
    """

    waveform: Waveform


@dataclass(frozen=True)
class Scale(Waveform):
    """
    <scale> ::= <scalar expr> '*' <waveform>
    """

    scalar: Scalar
    waveform: Waveform


@dataclass(frozen=True)
class Add(Waveform):
    """
    <add> ::= <waveform> '+' <waveform>
    """

    left: Waveform
    right: Waveform
