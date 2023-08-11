from typing import Union, Optional
from .waveform import WaveformAttachable
from .base import Builder, DefaultBuilderEncoder
from ..ir import Scalar

ScalarType = Union[float, str, Scalar]


class SpatialModulation(WaveformAttachable):
    pass


class Uniform(SpatialModulation):
    pass


class Location(SpatialModulation):
    __match_args__ = ("_label", "__parent__")

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
    __match_args__ = ("_value", "__parent__")

    def __init__(self, value: ScalarType, parent: Optional[Builder] = None) -> None:
        assert isinstance(value, (float, str, Scalar))
        super().__init__(parent)
        self._value = value


class Var(SpatialModulation):
    __match_args__ = ("_name", "__parent__")

    def __init__(self, name: str, parent: Optional[Builder] = None) -> None:
        assert isinstance(name, str)
        super().__init__(parent)
        self._name = name


class SpatialSerializer(DefaultBuilderEncoder):
    def default(self, obj):
        match obj:
            case Uniform(parent):
                return dict(type="Uniform", parent=self.default(parent))
            case Var(name, parent):
                return dict(type="Var", name=name, parent=self.default(parent))
            case Scale(factor, parent):
                return dict(type="Scale", factor=factor, parent=self.default(parent))
            case Location(label, parent):
                return dict(type="Location", label=label, parent=self.default(parent))
            case _:
                return super().default(obj)
