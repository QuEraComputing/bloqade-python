from .base import Builder
from .spatial import SpatialModulation
from bloqade.ir.control.pulse import rabi


class Detuning(SpatialModulation):
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

    pass


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
    def amplitude(self):
        """specify the amplitude of the rabi field.

        Examples:

            - rydberg coupling rabi amplitude
            (See also [`Amplitude`][bloqade.builder.field.Amplitude])

            >>> ryd_rabi = bloqade.start.rydberg.rabi
            >>> ryd_rabi_amp = ryd_rabi.amplitude


            - hyperfine coupling rabi amplitude
            (See also [`Amplitude`][bloqade.builder.field.Amplitude])

            >>> hyp_rabi = bloqade.start.hyperfine.rabi
            >>> hyp_rabi_amp = hyp_rabi.amplitude

        """
        self.__build_cache__.field_name = rabi.amplitude
        return Amplitude(self)

    @property
    def phase(self):
        """specify the phase of the rabi field.

        Examples:

            - rydberg coupling rabi phase
            (See also [`Amplitude`][bloqade.builder.field.Phase])

            >>> ryd_rabi = bloqade.start.rydberg.rabi
            >>> ryd_rabi_ph = ryd_rabi.phase


            - hyperfine coupling rabi phase
            (See also [`Amplitude`][bloqade.builder.field.Phase])

            >>> hyp_rabi = bloqade.start.hyperfine.rabi
            >>> hyp_rabi_ph = hyp_rabi.phase

        """
        self.__build_cache__.field_name = rabi.phase
        return Phase(self)


class Amplitude(SpatialModulation):
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

    pass


class Phase(SpatialModulation):
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

    pass
