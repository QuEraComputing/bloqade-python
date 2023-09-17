from bloqade.builder.base import Builder
from beartype import beartype


class Field(Builder):
    @property
    def uniform(self):
        """
        - Addressing all atom locations for preceeding waveform
        - Next-step: <WaveForm>
        - Possible Next:

            -> `...uniform.linear()`
                :: apply linear waveform

            -> `...uniform.constant()`
                :: apply constant waveform

            -> `...uniform.ploy()`
                :: apply polynomial waveform

            -> `...uniform.apply()`
                :: apply pre-constructed waveform

            -> `...uniform.piecewise_linear()`
                :: apply piecewise linear waveform

            -> `...uniform.piecewise_constant()`
                :: apply piecewise constant waveform

            -> `...uniform.fn()`
                :: apply callable as waveform.


        Examples:

            - Addressing rydberg detuning to all atoms in the system with
            4 sites

            >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.uniform

        """
        from bloqade.builder.spatial import Uniform

        return Uniform(self)

    @beartype
    def location(self, label: int):
        """
        Addressing one or multiple specific location(s) for preceeding waveform.

        (See [`Location`][bloqade.builder.location.Location] for more details])

        Args:
            label (int): The label of the location to apply the following waveform to.

        Examples:

            - Addressing rydberg detuning to location 1 on a system with 4 sites.

            >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(1)

            - Addressing rydberg detuning on both location
            0 and 2 on a system with 4 sites.

            >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(1).location(2)

        Note:
            label index start with 0, and should be positive.

        - Possible Next <Location>:

            -> `...location(int).location(int)`
                :: adding location into current list

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
        from bloqade.builder.spatial import Location

        return Location(label, self)

    @beartype
    def var(self, name: str):
        """
        - Addressing atom location associate with given variable for preceeding waveform
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


        Examples:

            - Addressing rydberg detuning to atom location `myatom` in the system with
            4 sites

            >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.var('myatom')

        """
        from bloqade.builder.spatial import Var

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
