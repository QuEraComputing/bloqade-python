from typing import Optional, Union, List, Callable
from numbers import Real
from functools import reduce
from .base import Builder
from .route import WaveformRoute
from .. import ir

ScalarType = Union[float, str, ir.Scalar]


def assert_scalar(name, value) -> None:
    assert isinstance(
        value, (Real, str, ir.Scalar)
    ), f"{name} must be a float, str, or Scalar"


class WaveformAttachable(Builder):
    def linear(
        self, start: ScalarType, stop: ScalarType, duration: ScalarType
    ) -> "Linear":
        return Linear(start, stop, duration, self)

    def constant(self, value: ScalarType, duration: ScalarType) -> "Constant":
        return Constant(value, duration, self)

    def poly(self, coeffs: ScalarType, duration: ScalarType) -> "Poly":
        return Poly(coeffs, duration, self)

    def apply(self, wf: ir.Waveform) -> "Apply":
        return Apply(wf, self)

    def piecewise_linear(
        self, durations: List[ScalarType], values: List[ScalarType]
    ) -> "PiecewiseLinear":
        return PiecewiseLinear(durations, values, self)

    def piecewise_constant(
        self, durations: List[ScalarType], values: List[ScalarType]
    ) -> "PiecewiseConstant":
        return PiecewiseConstant(durations, values, self)

    def fn(self, fn: Callable, duration: ScalarType) -> "Fn":
        return Fn(fn, duration, self)


# NOTE: waveform can refer previous pulse notes
#       or continue to specify pragma options
class Waveform(WaveformRoute, WaveformAttachable):
    pass


# mixin for slice and record
class Slicible:
    __match_args__ = ("_start", "_stop", "__parent__")

    def slice(
        self,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
    ) -> "Slice":
        return Slice(start, stop, self)


class Recordable:
    __mathc_args__ = ("_name", "__parent__")

    def record(self, name: str) -> "Record":
        return Record(name, self)


class WaveformPrimitive(Waveform, Slicible, Recordable):
    def __bloqade_ir__(self):
        raise NotImplementedError


class Linear(WaveformPrimitive):
    __match_args__ = ("_start", "_stop", "_duration", "__parent__")

    def __init__(
        self,
        start: ScalarType,
        stop: ScalarType,
        duration: ScalarType,
        parent: Optional[Builder] = None,
    ) -> None:
        assert_scalar("start", start)
        assert_scalar("stop", stop)
        assert_scalar("duration", duration)

        super().__init__(parent)
        self._start = ir.cast(start)
        self._stop = ir.cast(stop)
        self._duration = ir.cast(duration)

    def __bloqade_ir__(self) -> ir.Linear:
        return ir.Linear(start=self._start, stop=self._stop, duration=self._duration)


class Constant(WaveformPrimitive):
    __match_args__ = ("_value", "_duration", "__parent__")

    def __init__(
        self, value: ScalarType, duration: ScalarType, parent: Optional[Builder] = None
    ) -> None:
        assert_scalar("value", value)
        assert_scalar("duration", duration)

        super().__init__(parent)
        self._value = ir.cast(value)
        self._duration = ir.cast(duration)

    def __bloqade_ir__(self) -> ir.Constant:
        return ir.Constant(value=self._value, duration=self._duration)


class Poly(WaveformPrimitive):
    __match_args__ = ("_coeffs", "_duration", "__parent__")

    def __init__(
        self,
        coeffs: List[ScalarType],
        duration: ScalarType,
        parent: Optional[Builder] = None,
    ) -> None:
        assert_scalar("coeffs", coeffs)
        assert_scalar("duration", duration)

        super().__init__(parent)
        self._coeffs = map(ir.cast, coeffs)
        self._duration = ir.cast(duration)

    def __bloqade_ir__(self):
        return ir.Poly(coeffs=self._coeffs, duration=self._duration)


class Apply(WaveformPrimitive):
    __match_args__ = ("_wf", "__parent__")

    def __init__(self, wf: ir.Waveform, parent: Optional[Builder] = None):
        super().__init__(parent)
        self._wf = wf

    def __bloqade_ir__(self):
        return self._wf


class PiecewiseLinear(WaveformPrimitive):
    __match_args__ = ("_durations", "_values", "__parent__")

    def __init__(
        self,
        durations: List[ScalarType],
        values: List[ScalarType],
        parent: Optional[Builder] = None,
    ):
        assert (
            len(durations) == len(values) - 1
        ), "durations and values must be the same length"

        super().__init__(parent)
        self._durations = map(ir.cast, durations)
        self._values = map(ir.cast, values)

    def __bloqade_ir__(self):
        iter = zip(self._values[:-1], self._values[1:], self._durations)
        wfs = map(lambda v0, v1, t: ir.Linear(start=v0, stop=v1, duration=t), iter)
        return reduce(lambda a, b: a.append(b), wfs)


class PiecewiseConstant(WaveformPrimitive):
    __match_args__ = ("_durations", "_values", "__parent__")

    def __init__(
        self,
        durations: List[ScalarType],
        values: List[ScalarType],
        parent: Optional[Builder] = None,
    ) -> None:
        assert len(durations) == len(
            values
        ), "durations and values must be the same length"
        super().__init__(parent)
        self._durations = map(ir.cast, durations)
        self._values = map(ir.cast, values)

    def __bloqade_ir__(self):
        iter = zip(self._values, self._durations)
        wfs = map(lambda v, t: ir.Constant(value=v, duration=t), iter)
        return reduce(lambda a, b: a.append(b), wfs)


class Fn(WaveformPrimitive):
    __match_args__ = ("_fn", "_duration", "__parent__")

    def __init__(
        self,
        fn: Callable,
        duration: ScalarType,
        parent: Optional[Builder] = None,
    ) -> None:
        assert_scalar("duration", duration)
        super().__init__(parent)
        self._fn = fn
        self._duration = ir.cast(duration)

    def __bloqade_ir__(self):
        return ir.PythonFn(self._fn, self._duration)


# NOTE: no double-slice or double-record
class Slice(Waveform, Recordable):
    __match_args__ = ("_start", "_stop", "__parent__")

    def __init__(
        self,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        # NOTE: this should no raise for None
        self._start = ir.scalar.trycast(start)
        self._stop = ir.scalar.trycast(stop)


class Record(Waveform, Slicible):  # record should not be sliceable
    __mathc_args__ = ("_name", "__parent__")

    def __init__(
        self,
        name: str,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._name = ir.var(name)
