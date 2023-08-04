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
        """
        Scale the preceeding waveform by the specified factor.

        Args:
            scale (float): The factor to scale (amplitude of)
            the preceeding waveform.

        Examples:

            - Scale the preceeding waveform that addressing location(0) by 1.2.

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> scaled = reg.rydberg.detuning.location(0).scale(1.2)

            - Scale multiple locations with different factors.
            (ex. loc 0 by 1.2, loc 1 by 0.5)

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(0)
            >>> loc = loc.scale(1.2).location(1).scale(0.5)

            - Scale multiple locations with the same factor. (ex. loc 0 and 1 by 1.2)

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> scaled = reg.rydberg.detuning.location(0).location(1).scale(1.2)


        - Possible Next <Location>:

            -> `...scale(float).location(int)`
                :: keep adding location into current list

        - Possible Next <WaveForm>:

            -> `...scale(float).linear()`
                :: apply linear waveform

            -> `...scale(float).constant()`
                :: apply constant waveform

            -> `...scale(float).ploy()`
                :: apply polynomial waveform

            -> `...scale(float).apply()`
                :: apply pre-constructed waveform(s)

            -> `...scale(float).piecewise_linear()`
                :: apply piecewise linear waveform

            -> `...scale(float).piecewise_constant()`
                :: apply piecewise constant waveform

            -> `...scale(float).fn()`
                :: apply callable as waveform.



        """
        return Scale(self, scale)

    def location(self, label: int):
        """
        Append another location to the current location(s)

        Args:
            label (int): The label of the location

        Examples:

            - Append location 1 to the current location 0.

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(0)
            >>> loc = loc.location(1)

            - One can keep appending by concatenating location()

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(0)
            >>> loc = loc.location(1).location(2)

        - Possible Next <Location>:

            -> `...location(int).location(int)`
                :: keep adding location into current list

            -> `...location(int).scale(float)`
                :: specify scaling factor to current location
                for the preceeding waveform

        - Possible Next <WaveForm>:

            -> `...location(int).linear()`
                :: apply linear waveform

            -> `...location(int).constant()`
                :: apply constant waveform

            -> `...location(int).ploy()`
                :: apply polynomial waveform

            -> `...location(int).apply()`
                :: apply pre-constructed waveform

            -> `...location(int).piecewise_linear()`
                :: apply piecewise linear waveform

            -> `...location(int).piecewise_constant()`
                :: apply piecewise constant waveform

            -> `...location(int).fn()`
                :: apply callable as waveform.


        """
        return Location(self, label)


class Scale(Waveform):
    def __init__(self, parent: Builder, scale) -> None:
        super().__init__(parent)
        self._scale = cast(scale)

    def location(self, label: int):
        """
        - Append another location to the current location after scale the previous one

        Args:
            label (int): The label of the location

        Examples:

            - Append location 1 after scale location 0 by 1.2.

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(0).scale(1.2)
            >>> loc = loc.location(1)

        - Possible Next <Location>:

            -> `...location(int).location(int)`
                :: keep adding location into current list

            -> `...location(int).scale(float)`
                :: specify scaling factor to current location
                for the preceeding waveform

        - Possible Next <WaveForm>:

            -> `...location(int).linear()`
                :: apply linear waveform

            -> `...location(int).constant()`
                :: apply constant waveform

            -> `...location(int).ploy()`
                :: apply polynomial waveform

            -> `...location(int).apply()`
                :: apply pre-constructed waveform

            -> `...location(int).piecewise_linear()`
                :: apply piecewise linear waveform

            -> `...location(int).piecewise_constant()`
                :: apply piecewise constant waveform

            -> `...location(int).fn()`
                :: apply callable as waveform.



        """
        return Location(self, label)


class Uniform(Waveform):
    """
    The node specify a uniform spacial modulation. Which is ready to apply waveform
    (See [`Waveform`][bloqade.builder.waveform] for available waveform options)

    Examples:

        - To hit this node from the start node:

        >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
        >>> loc = reg.rydberg.detuning.uniform

        - Apply Linear waveform:

        >>> wv = bloqade.ir.Linear(start=0,stop=1,duration=0.5)
        >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
        >>> loc = reg.rydberg.detuning.uniform.apply(wv)

    """

    pass


class Var(Waveform):
    def __init__(self, parent: Builder, name: str) -> None:
        super().__init__(parent)
        self._name = name
