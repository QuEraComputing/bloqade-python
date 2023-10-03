from typing import Optional, TYPE_CHECKING

from beartype import beartype
from bloqade.builder.typing import ScalarType
from bloqade.builder.waveform import WaveformAttachable
from bloqade.builder.base import Builder


if TYPE_CHECKING:
    from bloqade.ir.control.field import UniformModulation


class SpatialModulation(WaveformAttachable):
    pass


class Uniform(SpatialModulation):
    """
    The node specify a uniform spacial modulation. Which is ready to apply waveform
    (See [`Waveform`][bloqade.builder.waveform] for available waveform options)

    Examples:

        - To hit this node from the start node:

        >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
        >>> loc = reg.rydberg.detuning.uniform

        - Apply Linear waveform:

        >>> wv = bloqade.ir.Linear(start=0,stop=1,duration=0.5)
        >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
        >>> loc = reg.rydberg.detuning.uniform.apply(wv)

    """

    def __bloqade_ir__(self) -> "UniformModulation":
        from bloqade.ir import Uniform

        return Uniform


class Location(SpatialModulation):
    __match_args__ = ("_label", "__parent__")

    @beartype
    def __init__(self, label: int, parent: Optional[Builder] = None) -> None:
        assert isinstance(label, int) and label >= 0
        super().__init__(parent)
        self._label = label

    @beartype
    def location(self, label: int) -> "Location":
        """
        Append another `.location` to the current location(s)
        as part of a singular spatial modulation definition.

        ### Usage Example:
        ```
        # definep program
        >>> from bloqade.atom_arrangement import start
        >>> geometry = start.add_position([(0,0),(1,1),(3,3)])
        >>> prog = start.rydberg.rabi.amplitude.location(0)
        >>> chain_loc_prog = prog.location(1).location(2)
        # Atoms at indices 0, 1, and 2 will now be subject
        # to the upcoming waveform definition. Thus, the
        # multiple locations are part of a singular
        # spatial modulation.
        ```

        - Your next steps include:
        - Continuing to modify your current spatial modulation via:
            - `...location(int).location(int)`: To add another location
            - `...location(int).scale(float)`: To scale the upcoming waveform
        - You may also jump directly to specifying a waveform via:
            - `...location(int).linear(start, stop, duration)`:
                to append a linear waveform
            - `...location(int).constant(value, duration)`:
                to append a constant waveform
            - `...location(int)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...location(int)
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...location(int).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...location(int).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - `...location(int).fn(f(t,...))`:
                to append a waveform defined by a python function

        """
        return Location(label, self)

    @beartype
    def scale(self, value: ScalarType) -> "Scale":
        """
        Scale the subsequent waveform to be applied on a certain set of
        atoms specified by the current spatial modulation.

        ### ### Usage Examples:
        ```
        # define program
        >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
        # scale the subsequent waveform to be applied on atom 0 by 1.2
        >>> scaled = reg.rydberg.detuning.location(0).scale(1.2)
        # scale the waveform on multiple locations by different factors
        >>> loc = reg.rydberg.detuning.location(0)
        >>> loc = loc.scale(1.2).location(1).scale(0.5)
        # scale multiple locations with the same factor
        >>> scaled = reg.rydberg.detuning.location(0).location(1).scale(1.2)
        ```

        - Your next steps include:
        - Continuing to modify your current spatial modulation via:
            - `...scale(float).location(int)`: To add another location
        - You may also jump directly to specifying a waveform via:
            - `...scale(float).linear(start, stop, duration)`:
                to append a linear waveform
            - `...scale(float).constant(value, duration)`:
                to append a constant waveform
            - `...scale(float)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...scale(float)
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...scale(float).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...scale(float).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - `...scale(float).fn(f(t,...))`:
                to append a waveform defined by a python function
        """
        return Scale(value, self)


# NOTE: not a spatial modulation itself because it only modifies the
#       location of the previous spatial modulation
class Scale(WaveformAttachable):
    __match_args__ = ("_value", "__parent__")

    @beartype
    def __init__(self, value: ScalarType, parent: Optional[Builder] = None) -> None:
        super().__init__(parent)
        self._value = value

    @beartype
    def location(self, label: int) -> "Location":
        """
        Append another `.location` to the current location(s)
        as part of a singular spatial modulation definition.

        ### Usage Example:
        ```
        # definep program
        >>> from bloqade.atom_arrangement import start
        >>> geometry = start.add_position([(0,0),(1,1),(3,3)])
        >>> prog = start.rydberg.rabi.amplitude.location(0)
        >>> chain_loc_prog = prog.location(1).location(2)
        # Atoms at indices 0, 1, and 2 will now be subject
        # to the upcoming waveform definition. Thus, the
        # multiple locations are part of a singular
        # spatial modulation.
        ```

        - Your next steps include:
        - Continuing to modify your current spatial modulation via:
            - `...location(int).location(int)`: To add another location
            - `...location(int).scale(float)`: To scale the upcoming waveform
        - You may also jump directly to specifying a waveform via:
            - `...location(int).linear(start, stop, duration)`:
                to append a linear waveform
            - `...location(int).constant(value, duration)`:
                to append a constant waveform
            - `...location(int)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...location(int)
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...location(int).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...location(int).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - `...location(int).fn(f(t,...))`:
                to append a waveform defined by a python function

        """
        return Location(label, self)


class Var(SpatialModulation):
    __match_args__ = ("_name", "__parent__")

    @beartype
    def __init__(self, name: str, parent: Optional[Builder] = None) -> None:
        assert isinstance(name, str)
        super().__init__(parent)
        self._name = name
