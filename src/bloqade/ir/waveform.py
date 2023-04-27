from pydantic.dataclasses import dataclass
from typing import Union
from typing import List
from enum import Enum
from .shape import Shape
from .scalar import Scalar, Interval
from ..julia.prelude import *


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

    pass


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
