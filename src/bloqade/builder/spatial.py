from .base import Builder


class SpatialModulation(Builder):
    """
    SpatialModulation specifies which atom(s) should be addressed to apply the
    preceeding waveform ((See [`Waveform`][bloqade.builder.waveform]
    for available waveforms onward)

    """

    def location(self, label: int):
        """
        - Addressing one or multiple specific location(s) for preceeding waveform.
        - Possible Next <Location>:

            -> `...location(int).location(int)`
                :: adding location into current list

            -> `...location(int).scale(float)`
                :: specify scaling factor for the preceeding waveform

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


        (See [`Location`][bloqade.builder.location.Location] for more details])

        Args:
            label (int): The label of the location to apply the following waveform to.

        Examples:

            - Addressing rydberg detuning to location 1 on a system with 4 sites.

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(1)

            - Addressing rydberg detuning on both location
            0 and 2 on a system with 4 sites.

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.location(1).location(2)


        Note:
            label index start with 0, and should be positive.


        """
        from .location import Location

        return Location(self, label)

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

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.uniform

        """
        from .location import Uniform

        return Uniform(self)

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

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> loc = reg.rydberg.detuning.var('myatom')

        """
        from .location import Var

        return Var(self, name)
