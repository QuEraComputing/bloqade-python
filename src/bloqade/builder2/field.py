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
    pass


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
    pass


class RabiPhase(Field):
    pass
