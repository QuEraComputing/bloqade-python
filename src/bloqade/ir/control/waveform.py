from numbers import Real
from bloqade.builder.typing import ScalarType
from bloqade.ir.tree_print import Printer
from bloqade.ir.scalar import (
    Scalar,
    Interval,
    Variable,
    AssignedVariable,
    cast,
    var,
)

from bisect import bisect_left
from decimal import Decimal
from pydantic.dataclasses import dataclass
from beartype.typing import Any, Tuple, Union, List, Callable, Dict, Container
from beartype import beartype
from enum import Enum

import numpy as np
import inspect
import scipy.integrate as integrate
from bloqade.visualization import get_ir_figure
from bloqade.visualization import display_ir
from functools import cached_property


@beartype
def to_waveform(duration: ScalarType) -> Callable[[Callable], "PythonFn"]:
    # turn python function into a waveform instruction."""

    def waveform_wrapper(fn: Callable) -> "PythonFn":
        return PythonFn.create(fn, duration)

    return waveform_wrapper


class Side(str, Enum):
    Left = "left"
    Right = "right"


class Alignment(str, Enum):
    Left = "left_aligned"
    Right = "right_aligned"


@dataclass(frozen=True)
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

    def __call__(self, clock_s: float, **kwargs) -> float:
        return float(self.eval_decimal(Decimal(str(clock_s)), **kwargs))

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
        return get_ir_figure(self, **assignments)

    def _get_data(self, npoints, **assignments):
        from bloqade.analysis.common.assignment_scan import AssignmentScan

        assignments = AssignmentScan(assignments).emit(self)

        duration = float(self.duration(**assignments))
        times = np.linspace(0, duration, npoints + 1)
        values = [self.__call__(time, **assignments) for time in times]
        return times, values

    def show(self, **assignments):
        display_ir(self, assignments)

    def align(
        self,
        alignment: Union[str, Alignment],
        value: Union[None, Side, ScalarType] = None,
    ) -> "Waveform":
        if isinstance(self, AlignedWaveform):
            raise ValueError("Cannot align an aligned waveform")

        alignment = Alignment(alignment)

        if value is None:
            value = Side.Left if alignment is Alignment.Right else Side.Right

        if not isinstance(value, Side):
            value = cast(value)

        return self.canonicalize(AlignedWaveform(self, alignment, value))

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

    def record(
        self, variable_name: Union[str, Variable], side: Union[str, Side] = Side.Right
    ):
        return Record(self, cast(variable_name), Side(side))

    def __add__(self, other: "Waveform") -> "Waveform":
        if isinstance(other, Waveform):
            return self.canonicalize(Add(self, other))

        return NotImplemented

    # def __radd__(self, other: "Waveform") -> "Waveform":
    #     if isinstance(other, Waveform):
    #         return self.canonicalize(Add(self, other))

    #     return NotImplemented

    def __sub__(self, other: "Waveform") -> "Waveform":
        if isinstance(other, Waveform):
            return self + (-other)

        return NotImplemented

    # def __rsub__(self, other: "Waveform") -> "Waveform":
    #     if isinstance(other, Waveform):
    #         return other + (-self)

    #     return NotImplemented

    def __mul__(self, other: Any) -> "Waveform":
        return self.scale(cast(other))

    def __rmul__(self, other: Any) -> "Waveform":
        return self.scale(cast(other))

    def __truediv__(self, other: Any) -> "Waveform":
        return self.scale(1 / cast(other))

    def __str__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    @staticmethod
    def canonicalize(expr: "Waveform") -> "Waveform":
        if isinstance(expr, Append):
            new_waveforms = []
            for waveform in expr.waveforms:
                if isinstance(waveform, Append):
                    new_waveforms += waveform.waveforms
                elif waveform.duration == cast(0):
                    # skip zero duration waveforms
                    continue
                else:
                    new_waveforms.append(waveform)

            new_waveforms = list(map(Waveform.canonicalize, new_waveforms))
            if len(new_waveforms) == 0:
                return Constant(0, 0)
            elif len(new_waveforms) == 1:
                return new_waveforms[0]
            else:
                return Append(new_waveforms)
        elif isinstance(expr, Add):
            left = Waveform.canonicalize(expr.left)
            right = Waveform.canonicalize(expr.right)
            if left == right:
                return left.scale(2)
            if left.duration == cast(0):
                return right
            if right.duration == cast(0):
                return left
            else:
                return expr
        else:
            return expr

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def print_node(self):
        raise NotImplementedError


@dataclass(frozen=True)
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
    value: Union[Scalar, Side]

    @property
    def duration(self):
        return self.waveform.duration

    def print_node(self):
        return "AlignedWaveform"

    def children(self):
        annotated_children = {}
        annotated_children["Waveform"] = self.waveform

        if self.alignment == Alignment.Left:
            annotated_children["Alignment"] = "Left"
        elif self.alignment == Alignment.Right:
            annotated_children["Alignment"] = "Right"

        if isinstance(self.value, Scalar):
            annotated_children["Value"] = self.value
        elif self.value == Side.Left:
            annotated_children["Value"] = "Left"
        elif self.value == Side.Right:
            annotated_children["Value"] = "Right"

        return annotated_children


@dataclass(frozen=True)
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


@dataclass(init=False, frozen=True)
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
    duration: Scalar

    @beartype
    def __init__(self, start: ScalarType, stop: ScalarType, duration: ScalarType):
        object.__setattr__(self, "start", cast(start))
        object.__setattr__(self, "stop", cast(stop))
        object.__setattr__(self, "duration", cast(duration))

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        start_value = self.start(**kwargs)
        stop_value = self.stop(**kwargs)

        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        else:
            return (
                (stop_value - start_value) / self.duration(**kwargs)
            ) * clock_s + start_value

    def print_node(self):
        return "Linear"

    def children(self):
        return {"start": self.start, "stop": self.stop, "duration": self.duration}


@dataclass(init=False, frozen=True)
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
    duration: Scalar

    @beartype
    def __init__(self, value: ScalarType, duration: ScalarType):
        object.__setattr__(self, "value", cast(value))
        object.__setattr__(self, "duration", cast(duration))

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        constant_value = self.value(**kwargs)
        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        else:
            return constant_value

    def print_node(self):
        return "Constant"

    def children(self):
        return {"value": self.value, "duration": self.duration}


@dataclass(init=False, frozen=True)
class Poly(Instruction):
    """
    ```bnf
    <poly> ::= <scalar>+
    ```

    f(t=0:duration) = c[0] + c[1]t + c[2]t^2 + ... + c[n-1]t^n-1 + c[n]t^n

    Args:
        coeffs (Tuple[Scalar]): the coefficients c[] of the polynomial.
        duration (Scalar): the time span of the waveform.

    """

    coeffs: Tuple[Scalar, ...]
    duration: Scalar

    @beartype
    def __init__(self, coeffs: Container[ScalarType], duration: ScalarType):
        object.__setattr__(self, "coeffs", tuple(map(cast, coeffs)))
        object.__setattr__(self, "duration", cast(duration))

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        # b + x + x^2 + ... + x^n-1 + x^n
        if clock_s > self.duration(**kwargs):
            return Decimal(0)
        else:
            # call clock_s on each element of the scalars,
            # then apply the proper powers
            value = Decimal(0)
            power = Decimal(1)
            for scalar_expr in self.coeffs:
                value += scalar_expr(**kwargs) * power
                power *= clock_s

            return value

    def print_node(self) -> str:
        return "Poly"

    def children(self):
        # should have annotation for duration
        # then annotations for the polynomial terms and exponents

        annotated_coeffs = {}
        for i, coeff in enumerate(self.coeffs):
            if i == 0:
                annotated_coeffs["b"] = coeff
            elif i == 1:
                annotated_coeffs["t"] = coeff
            else:
                annotated_coeffs["t^" + str(i)] = coeff

        annotated_coeffs["duration"] = self.duration
        return annotated_coeffs


@dataclass(frozen=True)
class PythonFn(Instruction):
    """

    ```bnf
    <python-fn> ::= 'python-fn' <python function def> <scalar expr>
    ```
    """

    fn: Callable  # [[float, ...], float] # f(t) -> value
    duration: Scalar
    parameters: List[Union[Variable, AssignedVariable]]  # come from node inspect
    default_param_values: Dict[str, Decimal]

    @staticmethod
    def create(fn: Callable, duration: ScalarType) -> "PythonFn":
        signature = inspect.getfullargspec(fn)

        if signature.varargs is not None:
            raise ValueError("Cannot have `*args` in function definition")

        if signature.varkw is not None:
            raise ValueError("Cannot have `**kwargs` in function definition")

        # get default kwonly first:
        variables = []
        default_param_values = {}
        if signature.kwonlydefaults is not None:
            for name, value in signature.kwonlydefaults.items():
                if isinstance(value, (Real, Decimal)):
                    variables.append(name)
                    default_param_values[name] = Decimal(str(value))
                else:
                    raise ValueError(
                        f"Default value for parameter {name} is not Real or Decimal, "
                        "cannot convert to Variable."
                    )

        variables += signature.args[1:]
        variables += signature.kwonlyargs

        parameters = list(map(var, variables))
        duration = cast(duration)

        return PythonFn(fn, duration, parameters, default_param_values)

    @cached_property
    def _hash_value(self) -> int:
        return (
            hash(self.__class__)
            ^ hash(self.fn)
            ^ hash(self.duration)
            ^ hash(tuple(self.parameters))
            ^ hash(frozenset(self.default_param_values.items()))
        )

    def __hash__(self) -> int:
        return self._hash_value

    def eval_decimal(self, clock_s: Decimal, **assignments) -> Decimal:
        new_assignments = {**self.default_param_values, **assignments}

        if clock_s > self.duration(**new_assignments):
            return Decimal(0)

        kwargs = {
            param.name: float(param(**new_assignments)) for param in self.parameters
        }
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
        return {"duration": self.duration, **{p.name: p for p in self.parameters}}

    def sample(
        self, dt: ScalarType, interpolation: Union[str, "Interpolation"]
    ) -> "Sample":
        return Sample(self, interpolation, cast(dt))


@dataclass(frozen=True)
class SmoothingKernel:
    def __call__(self, value: float) -> float:
        raise NotImplementedError


class FiniteSmoothingKernel(SmoothingKernel):
    # kernel that is zero outside of (-1, 1)
    pass


class InfiniteSmoothingKernel(SmoothingKernel):
    # Kernel that is non-zero for all values
    pass


@dataclass(frozen=True)
class Gaussian(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.exp(-(value**2) / 2) / np.sqrt(2 * np.pi)


@dataclass(frozen=True)
class Logistic(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.exp(-(np.logaddexp(0, value) + np.logaddexp(0, -value)))


@dataclass(frozen=True)
class Sigmoid(InfiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (2 / np.pi) * np.exp(-np.logaddexp(-value, value))


@dataclass(frozen=True)
class Triangle(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.maximum(0, 1 - np.abs(value))


@dataclass(frozen=True)
class Uniform(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return np.asarray(np.abs(value) <= 1, dtype=np.float64).squeeze()


@dataclass(frozen=True)
class Parabolic(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (3 / 4) * np.maximum(0, 1 - value**2)


@dataclass(frozen=True)
class Biweight(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (15 / 16) * np.maximum(0, 1 - value**2) ** 2


@dataclass(frozen=True)
class Triweight(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (35 / 32) * np.maximum(0, 1 - value**2) ** 3


@dataclass(frozen=True)
class Tricube(FiniteSmoothingKernel):
    def __call__(self, value: float) -> float:
        return (70 / 81) * np.maximum(0, 1 - np.abs(value) ** 3) ** 3


@dataclass(frozen=True)
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


@dataclass(init=False, frozen=True)
class Smooth(Waveform):
    """
    ```bnf
    <smooth> ::= 'smooth' <kernel> <waveform>
    ```
    """

    radius: Scalar
    kernel: SmoothingKernel
    waveform: Waveform

    def __init__(self, radius, kernel, waveform):
        if isinstance(kernel, str):
            if kernel == "Gaussian":
                kernel = GaussianKernel
            elif kernel == "Logistic":
                kernel = LogisticKernel
            elif kernel == "Sigmoid":
                kernel = SigmoidKernel
            elif kernel == "Triangle":
                kernel = TriangleKernel
            elif kernel == "Uniform":
                kernel = UniformKernel
            elif kernel == "Parabolic":
                kernel = ParabolicKernel
            elif kernel == "Biweight":
                kernel = BiweightKernel
            elif kernel == "Triweight":
                kernel = TriweightKernel
            elif kernel == "Tricube":
                kernel = TricubeKernel
            elif kernel == "Cosine":
                kernel = CosineKernel
            else:
                raise ValueError(f"Invalid kernel: {kernel}")

        object.__setattr__(self, "radius", cast(radius))
        object.__setattr__(self, "kernel", kernel)
        object.__setattr__(self, "waveform", waveform)

    @property
    def duration(self):
        return self.waveform.duration

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

    def print_node(self):
        return f"Smooth: {self.kernel.__class__.__name__}"

    def children(self):
        return {"radius": self.radius, "waveform": self.waveform}


@dataclass(frozen=True)
class Slice(Waveform):
    """
    ```
    <slice> ::= <waveform> <scalar.interval>
    ```
    """

    waveform: Waveform
    interval: Interval

    @cached_property
    def duration(self):
        from bloqade.ir.scalar import Slice

        if self.interval.start is None and self.interval.stop is None:
            raise ValueError("Interval must have a start or stop value")

        return Slice(self.waveform.duration, self.interval)

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
        return [self.interval, self.waveform]


@dataclass(frozen=True)
class Append(Waveform):
    """
    ```bnf
    <append> ::= <waveform>+
    ```
    """

    waveforms: Tuple[Waveform, ...]

    @cached_property
    def duration(self):
        duration = cast(0.0)
        for waveform in self.waveforms:
            duration = duration + waveform.duration

        return duration

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        append_time = Decimal(0)
        for waveform in self.waveforms:
            duration = waveform.duration(**kwargs)

            if clock_s <= append_time + duration:
                return waveform.eval_decimal(clock_s - append_time, **kwargs)

            append_time += duration

        return Decimal(0)

    def print_node(self):
        return "Append"

    def children(self):
        return self.waveforms


@dataclass(frozen=True)
class Negative(Waveform):
    """
    ```bnf
    <negative> ::= '-' <waveform>
    ```
    """

    waveform: Waveform

    @property
    def duration(self):
        return self.waveform.duration

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return -self.waveform.eval_decimal(clock_s, **kwargs)

    def print_node(self):
        return "Negative"

    def children(self):
        return [self.waveform]


@dataclass(init=False, frozen=True)
class Scale(Waveform):
    """
    ```bnf
    <scale> ::= <scalar expr> '*' <waveform>
    ```
    """

    scalar: Scalar
    waveform: Waveform

    def __init__(self, scalar, waveform: Waveform):
        object.__setattr__(self, "scalar", cast(scalar))
        object.__setattr__(self, "waveform", waveform)

    @property
    def duration(self):
        return self.waveform.duration

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.scalar(**kwargs) * self.waveform.eval_decimal(clock_s, **kwargs)

    def print_node(self):
        return "Scale"

    def children(self):
        return [self.scalar, self.waveform]


@dataclass(frozen=True)
class Add(Waveform):
    """
    ```bnf
    <add> ::= <waveform> '+' <waveform>
    ```
    """

    left: Waveform
    right: Waveform

    @cached_property
    def duration(self):
        return self.left.duration.max(self.right.duration)

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.left(clock_s, **kwargs) + self.right(clock_s, **kwargs)

    def print_node(self):
        return "+"

    def children(self):
        return [self.left, self.right]


@dataclass(frozen=True)
class Record(Waveform):
    """
    ```bnf
    <record> ::= 'record' <waveform> <var> <side>
    ```
    """

    waveform: Waveform
    var: Variable
    side: Side = Side.Right

    @property
    def duration(self):
        return self.waveform.duration

    def eval_decimal(self, clock_s: Decimal, **kwargs) -> Decimal:
        return self.waveform(clock_s, **kwargs)

    def print_node(self):
        return "Record"

    def children(self):
        return {"Waveform": self.waveform, "Variable": self.var}


class Interpolation(str, Enum):
    Linear = "linear"
    Constant = "constant"


@dataclass(frozen=True)
class Sample(Waveform):
    """
    ```bnf
    <sample> ::= 'sample' <waveform> <interpolation> <scalar>
    ```
    """

    waveform: Waveform
    interpolation: Interpolation
    dt: Scalar

    @property
    def duration(self):
        return self.waveform.duration

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

        if self.interpolation is Interpolation.Linear:
            if i == 0:
                return values[i]
            else:
                slope = (values[i] - values[i - 1]) / (times[i] - times[i - 1])
                return slope * (clock_s - times[i - 1]) + values[i - 1]

        elif self.interpolation is Interpolation.Constant:
            if i == 0:
                return values[i]
            else:
                return values[i - 1]

    def print_node(self):
        return f"Sample {self.interpolation.value}"

    def children(self):
        return {"Waveform": self.waveform, "sample_step": self.dt}
