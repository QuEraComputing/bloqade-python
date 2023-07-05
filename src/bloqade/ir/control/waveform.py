from bisect import bisect_left
from dataclasses import InitVar
from decimal import Decimal
from pydantic.dataclasses import dataclass
from typing import Any, Tuple, Union, List, Callable
from enum import Enum


from ..tree_print import Printer
from ..scalar import Scalar, Interval, Variable, cast
from bokeh.plotting import figure
import numpy as np
import inspect
import scipy.integrate as integrate


def instruction(duration: Any) -> "PythonFn":
    """Turn python function into a waveform instruction."""

    def waveform_wrapper(fn: Callable) -> "PythonFn":
        return PythonFn(fn, duration)

    return waveform_wrapper


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

    def __call__(self, clock_s: float, **kwargs) -> float:
        return float(self.eval_decimal(Decimal(str(clock_s)), **kwargs))

    def __mul__(self, scalar: Scalar) -> "Waveform":
        return self.scale(cast(scalar))

    def __rmul__(self, scalar: Scalar) -> "Waveform":
        return self.scale(cast(scalar))

    def __add__(self, other: "Waveform"):
        return self.add(other)

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        raise NotImplementedError

    def add(self, other: "Waveform") -> "Waveform":
        return self.canonicalize(Add(self, other))

    def append(self, other: "Waveform") -> "Waveform":
        return self.canonicalize(Append([self, other]))

    def plot(self, **assignments):
        duration = self.duration(**assignments)
        times = np.linspace(0, duration, 1001)
        values = [self.__call__(time, **assignments) for time in times]
        fig = figure(width=250, height=250)
        fig.line(times, values)
        return fig

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

    def smooth(self, radius, kernel: "SmoothingKernel") -> "Waveform":
        return self.canonicalize(
            Smooth(kernel=kernel, waveform=self, radius=cast(radius))
        )

    def scale(self, value) -> "Waveform":
        return self.canonicalize(Scale(cast(value), self))

    def __neg__(self) -> "Waveform":
        return self.canonicalize(Negative(self))

    def __getitem__(self, s: slice) -> "Waveform":
        return self.canonicalize(Slice(self, Interval.from_slice(s)))

    def record(self, variable_name: str):
        return Record(self, Variable(variable_name))

    @property
    def duration(self) -> Scalar:
        if self._duration:
            return self._duration

        match self:
            case Instruction(duration=duration):
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
            case Append(waveforms=waveforms):
                duration = cast(0.0)
                for waveform in waveforms:
                    duration = duration + cast(waveform.duration)

                self._duration = duration
            case Sample(waveform=waveform, interpolation=_, dt=_):
                self._duration = waveform.duration
            case Smooth(waveform=waveform, kernel=_, radius=_):
                return waveform.duration
            case Record(waveform=waveform, var=_):
                return waveform.duration
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

    def print_node(self):
        return "AlignedWaveform"

    def children(self):
        annotated_children = {}
        annotated_children["Waveform"] = self.waveform

        match self.alignment:
            case Alignment.Left:
                annotated_children["Alignment"] = "Left"
            case Alignment.Right:
                annotated_children["Alignment"] = "Right"

        match self.value:
            case Scalar():
                annotated_children["Value"] = self.value
            case AlignedValue.Left:
                annotated_children["Value"] = "Left"
            case AlignedValue.Right:
                annotated_children["Value"] = "Right"

        return annotated_children

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class Instruction(Waveform):
    pass


@dataclass(init=False)
class Linear(Instruction):
    """
    <linear> ::= 'linear' <scalar expr> <scalar expr>
    """

    start: Scalar
    stop: Scalar
    duration: InitVar[Scalar]

    def __init__(self, start, stop, duration):
        self.start = cast(start)
        self.stop = cast(stop)
        self._duration = cast(duration)

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        start_value = self.start(**kwargs)
        stop_value = self.stop(**kwargs)

        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        else:
            return (
                (stop_value - start_value) / self.duration(**kwargs)
            ) * clock_s + start_value

    def __repr__(self) -> str:
        return (
            f"Linear(start={self.start!r}, stop={self.stop!r}, "
            f"duration={self.duration!r})"
        )

    def print_node(self):
        return "Linear"

    def children(self):
        return {"start": self.start, "stop": self.stop, "duration": self.duration}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False)
class Constant(Instruction):
    """
    <constant> ::= 'constant' <scalar expr>
    """

    value: Scalar
    duration: InitVar[Scalar]

    def __init__(self, value, duration):
        self.value = cast(value)
        self._duration = cast(duration)

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        constant_value = self.value(**kwargs)
        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        else:
            return constant_value

    def __repr__(self) -> str:
        return f"Constant(value={self.value!r}, duration={self.duration!r})"

    def print_node(self):
        return "Constant"

    def children(self):
        return {"value": self.value, "duration": self.duration}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False)
class Poly(Instruction):
    """
    <poly> ::= <scalar>+
    """

    checkpoints: List[Scalar]
    duration: InitVar[Scalar]

    def __init__(self, checkpoints, duration):
        self.checkpoints = cast(checkpoints)
        self._duration = cast(duration)

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        # b + x + x^2 + ... + x^n-1 + x^n
        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        else:
            # call clock_s on each element of the scalars,
            # then apply the proper powers
            value = Decimal(0)
            for exponent, scalar_expr in enumerate(self.checkpoints):
                value += scalar_expr(**kwargs) * clock_s**exponent

            return value

    def __repr__(self) -> str:
        return f"Poly({self.checkpoints!r}, {self.duration!r})"

    def print_node(self) -> str:
        return "Poly"

    def children(self):
        # should have annotation for duration
        # then annotations for the polynomial terms and exponents

        annotated_checkpoints = {}
        for i, checkpoint in enumerate(self.checkpoints):
            if i == 0:
                annotated_checkpoints["b"] = checkpoint
            elif i == 1:
                annotated_checkpoints["t"] = checkpoint
            else:
                annotated_checkpoints["t^" + str(i)] = checkpoint

        annotated_checkpoints["duration"] = self._duration

        return annotated_checkpoints

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False)
class PythonFn(Instruction):
    """
    <python-fn> ::= 'python-fn' <python function def> <scalar expr>
    """

    fn: Callable  # [[float, ...], float] # f(t) -> value
    parameters: List[str]  # come from ast inspect
    duration: InitVar[Scalar]

    def __init__(self, fn: Callable, duration: Any):
        self.fn = fn
        self._duration = cast(duration)

        signature = inspect.getfullargspec(fn)

        if signature.varargs is not None:
            raise ValueError("Cannot have varargs")

        if signature.varkw is not None:
            raise ValueError("Cannot have varkw")

        self.parameters = list(signature.args[1:]) + list(signature.kwonlyargs)

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        if clock_s > self.duration(**kwargs):
            return Decimal(0)

        return Decimal(
            self.fn(
                float(clock_s),
                **{k: float(kwargs[k]) for k in self.parameters if k in kwargs},
            )
        )

    def print_node(self):
        return f"PythonFn: {self.fn.__name__}"

    def children(self):
        return {"duration": self.duration}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False)
class SmoothingKernel:
    def __call__(self, value: float) -> float:
        raise NotImplementedError


class FiniteSmoothingKernel(SmoothingKernel):
    # kernel that is zero outside of (-1, 1)
    pass


class InfiniteSmoothingKernel(SmoothingKernel):
    # Kernel that is non-zero for all values
    pass


class Guassian(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.exp(-(value**2) / 2) / np.sqrt(2 * np.pi)


class Logistic(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        np.exp(-(np.logaddexp(0, value) + np.logaddexp(0, -value)))


class Sigmoid(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (2 / np.pi) * np.exp(-np.logaddexp(-value, value))


class Triangle(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.maximum(0, 1 - np.abs(value))


class Uniform(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.asarray(np.abs(value) <= 1, dtype=np.float64).squeeze()


class Parabolic(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (3 / 4) * np.maximum(0, 1 - value**2)


class Biweight(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (15 / 16) * np.maximum(0, 1 - value**2) ** 2


class Triweight(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (35 / 32) * np.maximum(0, 1 - value**2) ** 3


class Tricube(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (70 / 81) * np.maximum(0, 1 - np.abs(value) ** 3) ** 3


class Cosine(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.maximum(0, np.pi / 4 * np.cos(np.pi / 2 * value))


GuassianKernel = Guassian()
LogisticKernel = Logistic()
SigmoidKernel = Sigmoid()
TriangleKernel = Triangle()
UniformKernel = Uniform()
ParabolicKernel = Parabolic()
BiweightKernel = Biweight()
TriweightKernel = Triweight()
TricubeKernel = Tricube()
CosineKernel = Cosine()


@dataclass
class Smooth(Waveform):
    """
    <smooth> ::= 'smooth' <kernel> <waveform>
    """

    radius: Scalar
    kernel: SmoothingKernel
    waveform: Waveform

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        float_clock_s = float(clock_s)
        radius = float(self.radius(**kwargs))
        duration = float(self.duration(**kwargs))
        waveform_start = self.waveform(0, **kwargs)
        waveform_stop = self.waveform(float(duration), **kwargs)

        def waveform(clock: float) -> float:
            if clock < 0:
                return waveform_start
            elif clock > duration:
                return waveform_stop
            else:
                return self.waveform(clock, **kwargs)

        def integrade(s):
            return self.kernel(s) * waveform(radius * s + float_clock_s)

        if isinstance(self.kernel, FiniteSmoothingKernel):
            return integrate.quad(integrade, -1, 1, epsabs=1e-4, epsrel=1e-4)[0]
        elif isinstance(self.kernel, InfiniteSmoothingKernel):
            return integrate.quad(integrade, -np.inf, np.inf, epsabs=1e-4, epsrel=1e-4)[
                0
            ]
        else:
            raise ValueError(f"Invalid kernel: {self.kernel}")

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

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        if self.interval.start is None:
            start_time = Decimal(0)
        else:
            start_time = self.interval.start(**kwargs)
        return self.waveform.eval_decimal(clock_s + start_time, **kwargs)

    def print_node(self):
        return "Slice"

    def children(self):
        return [self.waveform, self.interval]

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class Append(Waveform):
    """
    <append> ::= <waveform>+
    """

    waveforms: List[Waveform]

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        append_time = Decimal(0)
        for waveform in self.waveforms:
            duration = waveform.duration(**kwargs)

            if clock_s < append_time + duration:
                return waveform.eval_decimal(clock_s - append_time, **kwargs)

            append_time += duration

        return Decimal(0)

    def __repr__(self) -> str:
        return f"waveform.Append(waveforms={self.waveforms!r})"

    def print_node(self):
        return "Append"

    def children(self):
        return self.waveforms

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class Negative(Waveform):
    """
    <negative> ::= '-' <waveform>
    """

    waveform: Waveform

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return -self.waveform.eval_decimal(clock_s, **kwargs)

    def __repr__(self) -> str:
        return f"-({self.waveform!r})"

    def print_node(self):
        return "-"

    def children(self):
        return [self.waveform]

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False)
class Scale(Waveform):
    """
    <scale> ::= <scalar expr> '*' <waveform>
    """

    scalar: Scalar
    waveform: Waveform

    def __init__(self, scalar, waveform: Waveform):
        self.scalar = cast(scalar)
        self.waveform = waveform

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.scalar(**kwargs) * self.waveform.eval_decimal(clock_s, **kwargs)

    def __repr__(self) -> str:
        return f"({self.scalar!r} * {self.waveform!r})"

    def print_node(self):
        return "Scale"

    def children(self):
        return [self.scalar, self.waveform]

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class Add(Waveform):
    """
    <add> ::= <waveform> '+' <waveform>
    """

    left: Waveform
    right: Waveform

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.left(clock_s, **kwargs) + self.right(clock_s, **kwargs)

    def __repr__(self) -> str:
        return f"({self.left!r} + {self.right!r})"

    def print_node(self):
        return "+"

    def children(self):
        return [self.left, self.right]

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class Record(Waveform):
    """
    <record> ::= 'record' <waveform> <var>
    """

    waveform: Waveform
    var: Variable

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.waveform(clock_s, **kwargs)

    def print_node(self):
        return "Record"

    def children(self):
        return {"Waveform": self.waveform, "Variable": self.var}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


class Interpolation(str, Enum):
    Linear = "linear"
    Constant = "constant"


@dataclass
class Sample(Waveform):
    """
    <sample> ::= 'sample' <waveform> <interpolation> <scalar>
    """

    waveform: Waveform
    interpolation: Interpolation
    dt: Scalar

    def samples(self, **kwargs) -> Tuple[List[Decimal], List[Decimal]]:
        duration = self.duration(**kwargs)
        dt = self.dt(**kwargs)

        clock = Decimal("0.0")
        clocks = []
        values = []
        while clock < duration - dt:
            values.append(self.waveform.eval_decimal(clock, **kwargs))
            clocks.append(clock)
            clock += dt

        values.append(self.waveform.eval_decimal(duration, **kwargs))
        clocks.append(duration)

        return clocks, values

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        times = self.sample_times(**kwargs)

        i = bisect_left(times, clock_s)

        if i == len(times):
            return Decimal(0)

        match self.interpolation:
            case Interpolation.Linear:
                return self._linear_interpolation(
                    clock_s, times[i], times[i + 1], **kwargs
                )
            case Interpolation.Constant:
                return self._constant_interpolation(times[i], **kwargs)
            case _:
                raise ValueError("No interpolation specified")

    def _linear_interpolation(
        self, clock_s: Decimal, start_time: Decimal, stop_time: Decimal, **kwargs
    ) -> Decimal:
        start_value = self.waveform.eval_decimal(start_time, **kwargs)
        stop_value = self.waveform.eval_decimal(stop_time, **kwargs)
        slope = (stop_value - start_value) / (stop_time - start_time)

        return float(slope) * (clock_s - float(start_time)) + float(start_value)

    def _constant_interpolation(self, start_time: Decimal, **kwargs) -> Decimal:
        return self.waveform(start_time, **kwargs)

    def print_node(self):
        return f"Sample {self.interpolation}"

    def children(self):
        return {"Waveform": self.waveform, "sample_step": self.dt}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)
