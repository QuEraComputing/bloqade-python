from .base import Builder


class Field(Builder):
    @property
    def uniform(self):
        from .spatial import Uniform

        return Uniform(self)

    def location(self, label: int):
        from .spatial import Location

        return Location(label, self)

    def var(self, name: str):
        from .spatial import Var

        return Var(name, self)


class Detuning(Field):
    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import detuning

        return detuning


# this is just an eye candy, thus
# it's not the actual Field object
# one can skip this node when doing
# compilation
class Rabi(Builder):
    @property
    def amplitude(self) -> "RabiAmplitude":
        return RabiAmplitude(self)

    @property
    def phase(self) -> "RabiPhase":
        return RabiPhase(self)


class RabiAmplitude(Field):
    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.amplitude


class RabiPhase(Field):
    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.phase
