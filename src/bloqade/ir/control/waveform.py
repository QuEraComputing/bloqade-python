from ..tree_print import Printer
from ..scalar import Scalar, Interval, Literal, Variable, DefaultVariable, cast, var

from bisect import bisect_left
from dataclasses import InitVar
from decimal import Decimal
from pydantic.dataclasses import dataclass
from typing import Any, Tuple, Union, List, Callable
from enum import Enum

from bokeh.plotting import figure, show
import numpy as np
import inspect
import scipy.integrate as integrate


def instruction(duration: Any) -> "PythonFn":
    # turn python function into a waveform instruction."""

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
    Waveform node in the IR.

    - [`<instruction>`][bloqade.ir.control.waveform.Instruction]
    - [`<smooth>`][bloqade.ir.control.waveform.Smooth]
    - [`<slice>`][bloqade.ir.control.waveform.Slice]
    - [`<apppend>`][bloqade.ir.control.waveform.Append]
    - [`<negative>`][bloqade.ir.control.waveform.Negative]
    - [`<scale>`][bloqade.ir.control.waveform.Scale]
    - [`<add>`][bloqade.ir.control.waveform.Add]
    - [`<record>`][bloqade.ir.control.waveform.Record]
    - [`<sample>`][bloqade.ir.control.waveform.Sample]

    ```bnf
    <waveform> ::= <instruction>
        | <smooth>
        | <slice>
        | <append>
        | <negative>
        | <scale>
        | <add>
        | <record>
        | <sample>
    ```
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

    def figure(self, **assignments):
        """get figure of the plotting the waveform.

        Returns:
            figure: a bokeh figure
        """
        # Varlist = []
        duration = float(self.duration(**assignments))
        times = np.linspace(0, duration, 1001)
        values = [self.__call__(time, **assignments) for time in times]
        fig = figure(
            sizing_mode="stretch_both",
            x_axis_label="Time (s)",
            y_axis_label="Waveform(t)",
            tools="hover",
        )
        fig.line(times, values)

        return fig

    def _get_data(self, npoints, **assignments):
        duration = float(self.duration(**assignments))
        times = np.linspace(0, duration, npoints + 1)
        values = [self.__call__(time, **assignments) for time in times]
        return times, values

    def show(self, **assignments):
        show(self.figure(**assignments))

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

    def record(self, variable_name: Union[str, Variable]):
        return Record(self, cast(variable_name))

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

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def print_node(self):
        raise NotImplementedError


@dataclass(repr=False)
class AlignedWaveform(Waveform):
    """

    ```bnf
    <padded waveform> ::= <waveform> | <waveform> <alignment> <value>

    <alignment> ::= 'left aligned' | 'right aligned'
    <value> ::= 'left value' | 'right value' | <scalar expr>
    ```
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


@dataclass(repr=False)
class Instruction(Waveform):
    """Instruction node in the IR.

    - [`<linear>`][bloqade.ir.control.waveform.Linear]
    - [`<constant>`][bloqade.ir.control.waveform.Constant]
    - [`<poly>`][bloqade.ir.control.waveform.Poly]
    - [`<python-fn>`][bloqade.ir.control.waveform.PythonFn]


    ```bnf
    <instruction> ::= <linear>
        | <constant>
        | <poly>
        | <python-fn>
    ```
    """

    pass


@dataclass(init=False, repr=False)
class Linear(Instruction):
    """
    ```bnf
    <linear> ::= 'linear' <scalar expr> <scalar expr>
    ```

    f(t=0:duration) = start + (stop-start)/duration * t

    Args:
        start (Scalar): start value
        stop (Scalar): stop value
        duration (Scalar): the time span of the linear waveform.

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

    def __str__(self):
        return (
            f"Linear(start={str(self.start)}, stop={str(self.stop)}, "
            f"duration={str(self.duration)})"
        )

    def print_node(self):
        return "Linear"

    def children(self):
        return {"start": self.start, "stop": self.stop, "duration": self.duration}


@dataclass(init=False, repr=False)
class Constant(Instruction):
    """
    ```bnf
    <constant> ::= 'constant' <scalar expr>
    ```

    f(t=0:duration) = value

    Args:
        value (Scalar): the constant value
        duration (Scalar): the time span of the constant waveform.

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

    def __str__(self):
        return f"Constant(value={str(self.value)}, duration={str(self.duration)})"

    def print_node(self):
        return "Constant"

    def children(self):
        return {"value": self.value, "duration": self.duration}


@dataclass(init=False, repr=False)
class Poly(Instruction):
    """
    ```bnf
    <poly> ::= <scalar>+
    ```

    f(t=0:duration) = c[0] + c[1]t + c[2]t^2 + ... + c[n-1]t^n-1 + c[n]t^n

    Args:
        checkpoints (List[Scalar]): the coefficients c[] of the polynomial.
        duration (Scalar): the time span of the waveform.

    """

    coeffs: List[Scalar]
    duration: InitVar[Scalar]

    def __init__(self, coeffs, duration):
        self.coeffs = list(map(cast, coeffs))
        self._duration = cast(duration)

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        # b + x + x^2 + ... + x^n-1 + x^n
        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        else:
            # call clock_s on each element of the scalars,
            # then apply the proper powers
            value = Decimal(0)
            for exponent, scalar_expr in enumerate(self.coeffs):
                value += scalar_expr(**kwargs) * clock_s**exponent

            return value

    def __str__(self):
        return f"Poly({str(self.coeffs)}, {str(self.duration)})"

    def print_node(self) -> str:
        return "Poly"

    def children(self):
        # should have annotation for duration
        # then annotations for the polynomial terms and exponents

        annotated_checkpoints = {}
        for i, checkpoint in enumerate(self.coeffs):
            if i == 0:
                annotated_checkpoints["b"] = checkpoint
            elif i == 1:
                annotated_checkpoints["t"] = checkpoint
            else:
                annotated_checkpoints["t^" + str(i)] = checkpoint

        annotated_checkpoints["duration"] = self._duration

        return annotated_checkpoints


@dataclass(init=False, repr=False)
class PythonFn(Instruction):
    """

    ```bnf
    <python-fn> ::= 'python-fn' <python function def> <scalar expr>
    ```
    """

    fn: Callable  # [[float, ...], float] # f(t) -> value
    parameters: List[Union[Variable, DefaultVariable, Literal]]  # come from ast inspect
    duration: InitVar[Scalar]

    def __init__(self, fn: Callable, duration: Any):
        self.fn = fn
        self._duration = cast(duration)

        signature = inspect.getfullargspec(fn)

        if signature.varargs is not None:
            raise ValueError("Cannot have varargs")

        if signature.varkw is not None:
            raise ValueError("Cannot have varkw")

        # get default kwonly first:
        default_variables = []
        if signature.kwonlydefaults is not None:
            default_variables = [
                DefaultVariable(name, cast(Decimal(str(value))))
                for name, value in signature.kwonlydefaults.items()
            ]

        variables = signature.args[1:] + [
            v for v in signature.kwonlyargs if v not in signature.kwonlydefaults.keys()
        ]
        self.parameters = list(map(var, variables)) + default_variables

    def eval_decimal(self, clock_s: Decimal, **assignments) -> Decimal:
        if clock_s > self.duration(**assignments):
            return Decimal(0)

        kwargs = {param.name: float(param(**assignments)) for param in self.parameters}

        return Decimal(
            str(
                self.fn(
                    float(clock_s),
                    **kwargs,
                )
            )
        )

    def print_node(self):
        return f"PythonFn: {self.fn.__name__}"

    def children(self):
        return {"duration": self.duration}


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


class Gaussian(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.exp(-(value**2) / 2) / np.sqrt(2 * np.pi)


class Logistic(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.exp(-(np.logaddexp(0, value) + np.logaddexp(0, -value)))


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


GaussianKernel = Gaussian()
LogisticKernel = Logistic()
SigmoidKernel = Sigmoid()
TriangleKernel = Triangle()
UniformKernel = Uniform()
ParabolicKernel = Parabolic()
BiweightKernel = Biweight()
TriweightKernel = Triweight()
TricubeKernel = Tricube()
CosineKernel = Cosine()


@dataclass(repr=False)
class Smooth(Waveform):
    """
    ```bnf
    <smooth> ::= 'smooth' <kernel> <waveform>
    ```
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

    def __str__(self):
        return f"Smooth(kernel={str(self.kernel)}, waveform={str(self.waveform)})"


@dataclass(repr=False)
class Slice(Waveform):
    """
    ```
    <slice> ::= <waveform> <scalar.interval>
    ```
    """

    waveform: Waveform
    interval: Interval

    def __str__(self):
        return f"{str(self.waveform)}[{str(self.interval)}]"

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


@dataclass(repr=False)
class Append(Waveform):
    """
    ```bnf
    <append> ::= <waveform>+
    ```
    """

    waveforms: List[Waveform]

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        append_time = Decimal(0)
        for waveform in self.waveforms:
            duration = waveform.duration(**kwargs)

            if clock_s <= append_time + duration:
                return waveform.eval_decimal(clock_s - append_time, **kwargs)

            append_time += duration

        return Decimal(0)

    def __str__(self):
        return f"waveform.Append(waveforms={str(self.waveforms)})"

    def print_node(self):
        return "Append"

    def children(self):
        return self.waveforms


@dataclass(repr=False)
class Negative(Waveform):
    """
    ```bnf
    <negative> ::= '-' <waveform>
    ```
    """

    waveform: Waveform

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return -self.waveform.eval_decimal(clock_s, **kwargs)

    def __str__(self):
        return f"-({str(self.waveform)})"

    def print_node(self):
        return "-"

    def children(self):
        return [self.waveform]


@dataclass(init=False, repr=False)
class Scale(Waveform):
    """
    ```bnf
    <scale> ::= <scalar expr> '*' <waveform>
    ```
    """

    scalar: Scalar
    waveform: Waveform

    def __init__(self, scalar, waveform: Waveform):
        self.scalar = cast(scalar)
        self.waveform = waveform

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.scalar(**kwargs) * self.waveform.eval_decimal(clock_s, **kwargs)

    def __str__(self):
        return f"({str(self.scalar)} * {str(self.waveform)})"

    def print_node(self):
        return "Scale"

    def children(self):
        return [self.scalar, self.waveform]


@dataclass(repr=False)
class Add(Waveform):
    """
    ```bnf
    <add> ::= <waveform> '+' <waveform>
    ```
    """

    left: Waveform
    right: Waveform

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.left(clock_s, **kwargs) + self.right(clock_s, **kwargs)

    def __str__(self):
        return f"({str(self.left)} + {str(self.right)})"

    def print_node(self):
        return "+"

    def children(self):
        return [self.left, self.right]


@dataclass(repr=False)
class Record(Waveform):
    """
    ```bnf
    <record> ::= 'record' <waveform> <var>
    ```
    """

    waveform: Waveform
    var: Variable

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.waveform(clock_s, **kwargs)

    def print_node(self):
        return "Record"

    def children(self):
        return {"Waveform": self.waveform, "Variable": self.var}

    def __str__(self):
        return f"Record({str(self.waveform)}, {str(self.var)})"


class Interpolation(str, Enum):
    Linear = "linear"
    Constant = "constant"


@dataclass(repr=False)
class Sample(Waveform):
    """
    ```bnf
    <sample> ::= 'sample' <waveform> <interpolation> <scalar>
    ```
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
        while clock <= duration - dt:
            values.append(self.waveform.eval_decimal(clock, **kwargs))
            clocks.append(clock)
            clock += dt

        values.append(self.waveform.eval_decimal(duration, **kwargs))
        clocks.append(duration)

        return clocks, values

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        times, values = self.samples(**kwargs)
        i = bisect_left(times, clock_s)

        if i == len(times):
            return Decimal(0)

        match self.interpolation:
            case Interpolation.Linear:
                if i == 0:
                    return values[i]
                else:
                    slope = (values[i] - values[i - 1]) / (times[i] - times[i - 1])
                    return slope * (clock_s - times[i - 1]) + values[i - 1]

            case Interpolation.Constant:
                if i == 0:
                    return values[i]
                else:
                    return values[i - 1]
            case _:
                raise ValueError("No interpolation specified")

    def print_node(self):
        return f"Sample {self.interpolation.value}"

    def children(self):
        return {"Waveform": self.waveform, "sample_step": self.dt}
