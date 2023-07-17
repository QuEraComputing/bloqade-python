from .base import Builder


class SpatialModulation(Builder):
    def location(self, label: int):
        """apply the following waveform to the specified location."""
        from .location import Location

        return Location(self, label)

    @property
    def uniform(self):
        """applying the following waveform to all locations."""
        from .location import Uniform

        return Uniform(self)

    def var(self, name: str):
        """apply the following waveform to the variable location."""
        from .location import Var

        return Var(self, name)
