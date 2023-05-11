from .base import Builder


class SpatialModulation(Builder):
    def location(self, label: int):
        from .location import Location

        return Location(self, label)

    @property
    def uniform(self):
        from .location import Uniform

        return Uniform(self)

    def var(self, name: str):
        from .location import Var

        return Var(self, name)
