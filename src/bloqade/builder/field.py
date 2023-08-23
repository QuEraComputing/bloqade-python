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
    """
    This node represent detuning field of a
    specified level coupling (rydberg or hyperfine) type.


    Examples:

        - To specify detuning of rydberg coupling:

        >>> node = bloqade.start.rydberg.detuning
        >>> type(node)
        <class 'bloqade.builder.field.Detuning'>

        - To specify detuning of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.detuning
        >>> type(node)
        <class 'bloqade.builder.field.Detuning'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import detuning

        return detuning


# this is just an eye candy, thus
# it's not the actual Field object
# one can skip this node when doing
# compilation
class Rabi(Builder):
    """
    This node represent rabi field of a
    specified level coupling (rydberg or hyperfine) type.

    Examples:

        - To specify rabi of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi
        <class 'bloqade.builder.field.Rabi'>

        - To specify rabi of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi
        >>> type(node)
        <class 'bloqade.builder.field.Rabi'>


    """

    @property
    def amplitude(self) -> "RabiAmplitude":
        """
        - Specify the amplitude of the rabi field.
        - Next-step: <SpacialModulation>
        - Possible Next:

            -> `...amplitude.location(int)`
                :: Address atom at specific location

            -> `...amplitude.uniform`
                :: Address all atoms in register

            -> `...amplitude.var(str)`
                :: Address atom at location labeled by variable


        Examples:

            - rydberg coupling rabi amplitude
            (See also [`RabiAmplitude`][bloqade.builder.field.RabiAmplitude])

            >>> ryd_rabi = bloqade.start.rydberg.rabi
            >>> ryd_rabi_amp = ryd_rabi.amplitude


            - hyperfine coupling rabi amplitude
            (See also [`RabiAmplitude`][bloqade.builder.field.RabiAmplitude])

            >>> hyp_rabi = bloqade.start.hyperfine.rabi
            >>> hyp_rabi_amp = hyp_rabi.amplitude

        """
        return RabiAmplitude(self)

    @property
    def phase(self) -> "RabiPhase":
        """
        - Specify the phase of the rabi field.
        - Next-step: <SpacialModulation>
        - Possible Next:

            -> `...phase.location(int)`
                :: Address atom at specific location

            -> `...phase.uniform`
                :: Address all atoms in register

            -> `...phase.var(str)`
                :: Address atom at location labeled by variable


        Examples:

            - rydberg coupling rabi phase
            (See also [`RabiPhase`][bloqade.builder.field.RabiPhase])

            >>> ryd_rabi = bloqade.start.rydberg.rabi
            >>> ryd_rabi_ph = ryd_rabi.phase


            - hyperfine coupling rabi phase
            (See also [`RabiPhase`][bloqade.builder.field.RabiPhase])

            >>> hyp_rabi = bloqade.start.hyperfine.rabi
            >>> hyp_rabi_ph = hyp_rabi.phase

        """
        return RabiPhase(self)


class RabiAmplitude(Field):
    """
    This node represent amplitude of a rabi field.

    Examples:

        - To specify rabi amplitude of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi.amplitude
        >>> type(node)
        <class 'bloqade.builder.field.Amplitude'>

        - To specify rabi amplitude of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi.amplitude
        >>> type(node)
        <class 'bloqade.builder.field.Amplitude'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.amplitude


class RabiPhase(Field):
    """
    This node represent phase of a rabi field.

    Examples:

        - To specify rabi phase of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi.phase
        >>> type(node)
        <class 'bloqade.builder.field.Phase'>

        - To specify rabi phase of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi.phase
        >>> type(node)
        <class 'bloqade.builder.field.Phase'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.
    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.phase
