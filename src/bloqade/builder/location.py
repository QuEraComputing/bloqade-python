from .base import Builder
from .waveform import Waveform
from bloqade.ir import cast


# NOTE: waveform can be specified only after
# 1. location
# 2. scale
# 3. uniform
# 4. var
class Location(Waveform):
    def __init__(self, parent: Builder, label: int) -> None:
        super().__init__(parent)
        self._label = label

    def scale(self, scale: float):
        return Scale(self, scale)

    def location(self, label: int):
        return Location(self, label)


class Scale(Waveform):
    def __init__(self, parent: Builder, scale) -> None:
        super().__init__(parent)
        self._scale = cast(scale)

    def location(self, label: int):
        return Location(self, label)


class Uniform(Waveform):
    pass


class Var(Waveform):
    def __init__(self, parent: Builder, name: str) -> None:
        super().__init__(parent)
        self._name = name
