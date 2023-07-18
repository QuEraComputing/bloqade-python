from .base import Builder
from .terminate import Terminate
import bloqade.ir as ir
from typing import Union, List, Callable, Optional

ScalarType = Union[float, str]


class Waveform(Builder):
    def linear(self, start: ScalarType, stop: ScalarType, duration: ScalarType):
        """append a linear waveform to the current location."""
        return Linear(self, start, stop, duration)

    def constant(self, value: ScalarType, duration: ScalarType):
        """append a constant waveform to the current location."""
        return Constant(self, value, duration)

    def poly(self, coeffs: ScalarType, duration: ScalarType):
        """append a polynomial waveform to the current location."""
        return Poly(self, coeffs, duration)

    def apply(self, wf: ir.Waveform):
        """apply a pre-defined waveform to the current location."""
        return Apply(self, wf)

    def piecewise_linear(self, durations: List[ScalarType], values: List[ScalarType]):
        """append a piecewise linear waveform to the current location."""
        builder = self
        if len(durations) != len(values) - 1:
            raise ValueError("len(durations) must be len(values)-1.")

        for duration, start, stop in zip(durations, values[:-1], values[1:]):
            builder = builder.linear(start, stop, duration)

        return builder

    def piecewise_constant(self, durations: List[ScalarType], values: List[ScalarType]):
        """append a piecewise constant waveform to the current location."""
        builder = self
        if len(durations) != len(values):
            raise ValueError("durations and values lists must have same length.")

        for duration, value in zip(durations, values):
            builder = builder.constant(value, duration)

        return builder

    def fn(self, fn: Callable, duration: ScalarType):
        """append a waveform defined by a python function to the current location."""
        return PythonFn(self, fn, duration)


class WaveformTerminate(Waveform, Terminate):
    pass


class Sliceable:
    def slice(
        self, start: Optional[ScalarType] = None, stop: Optional[ScalarType] = None
    ):
        """slice the current waveform."""
        return Slice(self, start, stop)


class Recordable:
    def record(self, name: str):
        """record the value of the current waveform to a variable."""
        return Record(self, name)


class Apply(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, builder: Builder, wf: ir.Waveform) -> None:
        super().__init__(builder)
        self._waveform = wf


class Linear(Sliceable, Recordable, WaveformTerminate):
    def __init__(
        self, parent: Builder, start: float, stop: float, duration: str
    ) -> None:
        super().__init__(parent)
        self._waveform = ir.Linear(start, stop, duration)


class Constant(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, parent: Builder, value: float, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.Constant(value, duration)


class Poly(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, parent: Builder, coeffs: list, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.Poly(coeffs, duration)


class PythonFn(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, parent: Builder, fn: Callable, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.PythonFn(fn, duration)

    def sample(
        self,
        dt: ScalarType,
        interpolation: Optional[Union[ir.Interpolation, str]] = None,
    ) -> "Sample":
        """sample the current waveform at the specified time interval."""
        if interpolation is not None:
            return Sample(self, dt, interpolation=interpolation)

        match self.__build_cache__.field_name:
            case ir.control.pulse.rabi.amplitude | ir.control.pulse.detuning:
                return Sample(self, dt, interpolation=ir.Interpolation.Linear)
            case ir.control.pulse.rabi.phase:
                return Sample(self, dt, interpolation=ir.Interpolation.Constant)
            case _:
                raise NotImplementedError(
                    f"Sampling for {self.__build_cache__.field_name} is not implemented"
                )


class Sample(Sliceable, Recordable, WaveformTerminate):
    def __init__(
        self,
        parent: Builder,
        dt: ScalarType,
        interpolation: Union[ir.Interpolation, str],
    ) -> None:
        super().__init__(parent)
        self._dt = ir.cast(dt)
        self._interpolation = ir.Interpolation(interpolation)


class Slice(Recordable, WaveformTerminate):  # slice should not be sliceable
    def __init__(
        self,
        parent: Builder,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
    ) -> None:
        super().__init__(parent)
        self._start = ir.cast(start) if start is not None else None
        self._stop = ir.cast(stop) if stop is not None else None


class Record(WaveformTerminate):  # record should not be sliceable
    def __init__(
        self,
        parent: Builder,
        name: str,
    ) -> None:
        super().__init__(parent)
        self._name = name
