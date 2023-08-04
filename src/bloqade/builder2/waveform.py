from typing import Optional, Union, List, Callable
from .base import Builder
from .route import WaveformRoute
from .. import ir

ScalarType = Union[float, str, ir.Scalar]


def assert_scalar(name, value) -> None:
    assert isinstance(
        value, (float, str, ir.Scalar)
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
    def slice(
        self,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
    ) -> "Slice":
        return Slice(start, stop, self)


class Recordable:
    def record(self, name: str) -> "Record":
        return Record(name, self)


class WaveformPrimitive(Waveform, Slicible, Recordable):
    pass


class Linear(WaveformPrimitive):
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
        self._start = start
        self._stop = stop
        self._duration = duration


class Constant(WaveformPrimitive):
    def __init__(
        self, value: ScalarType, duration: ScalarType, parent: Optional[Builder] = None
    ) -> None:
        assert_scalar("value", value)
        assert_scalar("duration", duration)

        super().__init__(parent)
        self._value = value
        self._duration = duration


class Poly(WaveformPrimitive):
    def __init__(
        self, coeffs: ScalarType, duration: ScalarType, parent: Optional[Builder] = None
    ) -> None:
        assert_scalar("coeffs", coeffs)
        assert_scalar("duration", duration)

        super().__init__(parent)
        self._coeffs = coeffs
        self._duration = duration


class Apply(WaveformPrimitive):
    def __init__(self, wf: ir.Waveform, parent: Optional[Builder] = None):
        super().__init__(parent)
        self._wf = wf


class PiecewiseLinear(WaveformPrimitive):
    def __init__(
        self,
        durations: List[ScalarType],
        values: List[ScalarType],
        parent: Optional[Builder] = None,
    ):
        assert len(durations) == len(
            values
        ), "durations and values must be the same length"

        super().__init__(parent)
        self._durations = durations
        self._values = values


class PiecewiseConstant(WaveformPrimitive):
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
        self._durations = durations
        self._values = values


class Fn(WaveformPrimitive):
    def __init__(
        self,
        fn: Callable,
        duration: ScalarType,
        parent: Optional[Builder] = None,
    ) -> None:
        assert_scalar("duration", duration)
        super().__init__(parent)
        self._fn = fn
        self._duration = duration


# NOTE: no double-slice or double-record
class Slice(Waveform, Recordable):
    def __init__(
        self,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._start = start
        self._stop = stop


class Record(Waveform, Slicible):  # record should not be sliceable
    def __init__(
        self,
        name: str,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._name = name
