from typing import Union, Optional
from .waveform import WaveformAttachable
from .base import Builder
from ..ir import Scalar

ScalarType = Union[float, str, Scalar]


class SpatialModulation(WaveformAttachable):
    pass


class Uniform(SpatialModulation):
    pass


class Location(SpatialModulation):
    def __init__(self, label: int, parent: Optional[Builder] = None) -> None:
        assert isinstance(label, int) and label >= 0
        super().__init__(parent)
        self._label = label

    def location(self, label: int) -> "Location":
        return Location(label, self)

    def scale(self, value) -> "Scale":
        return Scale(value, self)


# NOTE: not a spatial modulation itself because it only modifies the
#       location of the previous spatial modulation
class Scale(WaveformAttachable):
    def __init__(self, value: ScalarType, parent: Optional[Builder] = None) -> None:
        assert isinstance(value, (float, str, Scalar))
        super().__init__(parent)
        self._value = value


class Var(SpatialModulation):
    def __init__(self, name: str, parent: Optional[Builder] = None) -> None:
        assert isinstance(name, str)
        super().__init__(parent)
        self._name = name
