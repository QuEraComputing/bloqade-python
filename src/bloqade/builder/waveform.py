from .base import Builder
from .terminate import Terminate
import bloqade.ir as ir


class Waveform(Builder):
    def linear(self, start: float, stop: float, duration: str):
        return Linear(self, start, stop, duration)

    def constant(self, value: float, duration: str):
        return Constant(self, value, duration)

    def poly(self, coeffs: list, duration: str):
        return Poly(self, coeffs, duration)

    def apply(self, wf: ir.Waveform):
        return Apply(self, wf)


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
        self._start = start
        self._stop = stop
        self._duration = duration


class Constant(WaveformTerminate):
    def __init__(self, parent: Builder, value: float, duration: str) -> None:
        super().__init__(parent)
        self._value = value
        self._duration = duration


class Poly(WaveformTerminate):
    def __init__(self, parent: Builder, coeffs: list, duration: str) -> None:
        super().__init__(parent)
        self._coeffs = coeffs
        self._duration = duration
