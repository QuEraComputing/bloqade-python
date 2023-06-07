from .base import Builder
from .terminate import Terminate
import bloqade.ir as ir
from typing import Union, List, Callable, Optional

ScalarType = Union[float, str]


class Waveform(Builder):
    def linear(self, start: ScalarType, stop: ScalarType, duration: ScalarType):
        return Linear(self, start, stop, duration)

    def constant(self, value: ScalarType, duration: ScalarType):
        return Constant(self, value, duration)

    def poly(self, coeffs: ScalarType, duration: ScalarType):
        return Poly(self, coeffs, duration)

    def apply(self, wf: ir.Waveform):
        return Apply(self, wf)

    def piecewise_linear(self, durations: List[ScalarType], values: List[ScalarType]):
        builder = self
        for duration, start, stop in zip(durations, values[:-1], values[1:]):
            builder = builder.linear(start, stop, duration)

        return builder

    def piecewise_constant(self, durations: List[ScalarType], values: List[ScalarType]):
        builder = self
        for duration, value in zip(durations, values):
            builder = builder.constant(value, duration)

        return builder

    def fn(self, fn: Callable, duration: ScalarType):
        return PythonFn(self, fn, duration)


class WaveformTerminate(Waveform, Terminate):
    pass


class Apply(WaveformTerminate):
    def __init__(self, builder: Builder, wf: ir.Waveform) -> None:
        super().__init__(builder)
        self._waveform = wf


class Linear(WaveformTerminate):
    def __init__(
        self, parent: Builder, start: float, stop: float, duration: str
    ) -> None:
        super().__init__(parent)
        self._waveform = ir.Linear(start, stop, duration)


class Constant(WaveformTerminate):
    def __init__(self, parent: Builder, value: float, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.Constant(value, duration)


class Poly(WaveformTerminate):
    def __init__(self, parent: Builder, coeffs: list, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.Poly(coeffs, duration)


class PythonFn(WaveformTerminate):
    def __init__(self, parent: Builder, fn: Callable, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.PythonFn(fn, duration)

    def sample(
        self, dt: ScalarType, interpolation: Optional[ir.Interpolation] = None
    ) -> "Sample":
        if interpolation is not None:
            return Sample(self, dt, interpolation=interpolation)

        if self.__build_cache__.field_name in [
            ir.pulse.rabi.amplitude,
            ir.pulse.detuning,
        ]:
            return Sample(self, dt, interpolation="linear")
        elif self.__build_cache__.field_name == ir.pulse.rabi.phase:
            return Sample(self, dt, interpolation="constant")
        else:
            raise NotImplementedError(
                f"Sampling for {self.__build_cache__.field_name} is not implemented"
            )


class Sample(WaveformTerminate):
    def __init__(self, parent: Builder, dt: ScalarType, interpolation: str) -> None:
        super().__init__(parent)
        self._dt = ir.cast(dt)
        self._interpolation = ir.Interpolation(interpolation)
