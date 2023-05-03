from dataclasses import InitVar
from pydantic.dataclasses import dataclass
from typing import Any, Union, List
from enum import Enum
from .scalar import Scalar, Interval, cast


class AlignedValue(str, Enum):
    Left = "left_value"
    Right = "right_value"


class Alignment(str, Enum):
    Left = "left_aligned"
    Right = "right_aligned"


@dataclass
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

    def __post_init__(self):
        self._duration = None

    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError

    def __mul__(self, scalar: Scalar) -> "Waveform":
        return self.scale(cast(scalar))

    def __rmul__(self, scalar: Scalar) -> "Waveform":
        return self.scale(cast(scalar))

    def __add__(self, other: "Waveform"):
        return self.add(other)

    def add(self, other: "Waveform") -> "Waveform":
        return self.canonicalize(Add(self, other))

    def append(self, other: "Waveform") -> "Waveform":
        return self.canonicalize(Append([self, other]))

    def align(
        self, alignment: Alignment, value: Union[None, AlignedValue, Scalar] = None
    ) -> "Waveform":
        if value is None:
            if alignment == Alignment.Left:
                value = AlignedValue.Left
            elif alignment == Alignment.Right:
                value = AlignedValue.Right
            else:
                raise ValueError(f"Invalid alignment: {alignment}")
        elif value is Scalar or value is AlignedValue:
            return self.canonicalize(AlignedWaveform(self, alignment, value))
        else:
            return self.canonicalize(AlignedWaveform(self, alignment, cast(value)))

    def smooth(self, kernel: str = "gaussian") -> "Waveform":
        return self.canonicalize(Smooth(kernel, self))

    def scale(self, value) -> "Waveform":
        return self.canonicalize(Scale(cast(value), self))

    def __neg__(self) -> "Waveform":
        return self.canonicalize(Negative(self))

    def __getitem__(self, s: slice) -> "Waveform":
        return self.canonicalize(Slice(self, Interval.from_slice(s)))

    @property
    def duration(self) -> Scalar:
        if self._duration:
            return self._duration

        match self:
            case Sequence(duration=duration):
                self._duration = duration
            case AlignedWaveform(waveform=waveform, alignment=_, value=_):
                self._duration = waveform.duration()
            case Slice(waveform=waveform, interval=interval):
                match (interval.start, interval.stop):
                    case (None, None):
                        raise ValueError(f"Cannot compute duration of {self}")
                    case (start, None):
                        self._duration = waveform.duration - start
                    case (None, stop):
                        self._duration = stop
                    case (start, stop):
                        self._duration = stop - start
            case _:
                raise ValueError(f"Cannot compute duration of {self}")
        return self._duration

    @staticmethod
    def canonicalize(expr: "Waveform") -> "Waveform":
        match expr:
            case Append([Append(lhs), Append(rhs)]):
                return Append(list(map(Waveform.canonicalize, lhs + rhs)))
            case Append([Append(waveforms), waveform]):
                return Waveform.canonicalize(Append(waveforms + [waveform]))
            case Append([waveform, Append(waveforms)]):
                return Waveform.canonicalize(Append([waveform] + waveforms))
            case _:
                return expr


@dataclass
class AlignedWaveform(Waveform):
    """
    <padded waveform> ::= <waveform> | <waveform> <alignment> <value>

    <alignment> ::= 'left aligned' | 'right aligned'
    <value> ::= 'left value' | 'right value' | <scalar expr>
    """

    waveform: Waveform
    alignment: Alignment
    value: Union[Scalar, AlignedValue]


@dataclass
class Sequence(Waveform):
    pass


@dataclass(init=False)
class Linear(Sequence):
    """
    <linear> ::= 'linear' <scalar expr> <scalar expr>
    """

    start: Scalar
    stop: Scalar
    duration: Scalar

    def __init__(self, start, stop, duration):
        self.start = cast(start)
        self.stop = cast(stop)
        self._duration = cast(duration)

    def __call__(self, clock_s: float, **kwargs) -> Any:
        start_value = self.start(**kwargs)
        stop_value = self.stop(**kwargs)

        if clock_s > self.duration(**kwargs):
            return 0.0
        else:
            return ((stop_value - start_value) / self.duration(**kwargs)) * clock_s

    def __repr__(self) -> str:
        return (
            f"Linear(start={self.start!r}, stop={self.stop!r}, "
            "duration={self.duration!r})"
        )


@dataclass(init=False)
class Constant(Sequence):
    """
    <constant> ::= 'constant' <scalar expr>
    """

    value: Scalar
    duration: InitVar[Scalar]

    def __init__(self, value, duration):
        self.value = cast(value)
        self._duration = cast(duration)

    def __call__(self, clock_s: float, **kwargs) -> Any:
        constant_value = self.value(**kwargs)
        if clock_s > self.duration(**kwargs):
            return 0.0
        else:
            return constant_value

    def __repr__(self) -> str:
        return f"Constant(value={self.value!r}, duration={self.duration!r})"


@dataclass(init=False)
class Poly(Sequence):
    """
    <poly> ::= <scalar>+
    """

    checkpoints: List[Scalar]
    duration: Scalar

    def __init__(self, checkpoints, duration):
        self.checkpoints = cast(checkpoints)
        self._duration = cast(duration)

    def __call__(self, clock_s: float, **kwargs) -> Any:
        # b + x + x^2 + ... + x^n-1 + x^n
        if clock_s > self.duration(**kwargs):
            return 0.0
        else:
            # call clock_s on each element of the scalars,
            # then apply the proper powers
            value = 0.0
            for exponent, scalar_expr in enumerate(self.checkpoints):
                value += scalar_expr(**kwargs) * clock_s**exponent

            return value

    def __repr__(self) -> str:
        return f"Poly({self.checkpoints!r}, {self.duration!r})"


@dataclass
class Smooth(Waveform):
    """
    <smooth> ::= 'smooth' <kernel> <waveform>
    """

    kernel: str
    waveform: Waveform

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"Smooth(kernel={self.kernel!r}, waveform={self.waveform!r})"


@dataclass
class Slice(Waveform):
    """
    <slice> ::= <waveform> <scalar.interval>
    """

    waveform: Waveform
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.waveform!r}[{self.interval!r}]"

    def __call__(self, clock_s: float, **kwargs) -> Any:
        if clock_s > self.duration(**kwargs):
            return 0.0

        start_time = self.interval.start(**kwargs)
        return self.waveform(clock_s + start_time, **kwargs)


@dataclass
class Append(Waveform):
    """
    <append> ::= <waveform>+
    """

    waveforms: List[Waveform]

    def __call__(self, clock_s: float, **kwargs) -> Any:
        append_time = 0.0
        for waveform in self.waveforms:
            duration = waveform.duration(**kwargs)

            if clock_s < append_time + duration:
                return waveform(clock_s - append_time, **kwargs)

            append_time += duration

        return 0.0

    def __repr__(self) -> str:
        return f"waveform.Append(waveforms={self.waveforms!r})"


@dataclass
class Negative(Waveform):
    """
    <negative> ::= '-' <waveform>
    """

    waveform: Waveform

    def __call__(self, clock_s: float, **kwargs) -> Any:
        return -self.waveform(clock_s, **kwargs)

    def __repr__(self) -> str:
        return f"-({self.waveform!r})"


@dataclass
class Scale(Waveform):
    """
    <scale> ::= <scalar expr> '*' <waveform>
    """

    scalar: Scalar
    waveform: Waveform

    def __init__(self, scalar, waveform: Waveform):
        self.scalar = cast(scalar)
        self.waveform = waveform

    def __call__(self, clock_s: float, **kwargs) -> Any:
        return self.scalar(**kwargs) * self.waveform(clock_s, **kwargs)

    def __repr__(self) -> str:
        return f"({self.scalar!r} * {self.waveform!r})"


@dataclass
class Add(Waveform):
    """
    <add> ::= <waveform> '+' <waveform>
    """

    left: Waveform
    right: Waveform

    def __call__(self, clock_s: float, **kwargs) -> Any:
        return self.left(clock_s, **kwargs) + self.right(clock_s, **kwargs)

    def __repr__(self) -> str:
        return f"({self.left!r} + {self.right!r})"
