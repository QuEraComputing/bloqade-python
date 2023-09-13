from bloqade.builder.coupling import Rydberg, Hyperfine


class Drive:
    @property
    def rydberg(self) -> Rydberg:
        """
        - Specify the Rydberg level coupling.
        - Possible Next:

            -> `...rydberg.rabi`
                :: address rabi term

            -> `...rydberg.detuning`
                :: address detuning field

        Examples:
            >>> node = bloqade.start.rydberg
            >>> type(node)
            <class 'bloqade.builder.coupling.Rydberg'>

            - Rydberg level coupling have two reachable field nodes:

                - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
                - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

            >>> ryd_detune = bloqade.start.rydberg.detuning
            >>> ryd_rabi = bloqade.start.rydberg.rabi

        See [`Rydberg`][bloqade.builder.coupling.Rydberg] for more details.
        """
        return Rydberg(self)

    @property
    def hyperfine(self) -> Hyperfine:
        """
        - Specify the Hyperfile level coupling.
        - Possible Next:

            -> `...hyperfine.rabi`
                :: address rabi term

            -> `...hyperfine.detuning`
                :: address detuning field


        Examples:
            >>> node = bloqade.start.hyperfine
            >>> type(node)
            <class 'bloqade.builder.coupling.Hyperfine'>

            - Hyperfine level coupling have two reachable field nodes:

                - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
                - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

            >>> hyp_detune = bloqade.start.hyperfine.detuning
            >>> hyp_rabi = bloqade.start.hyperfine.rabi


        See [Hyperfine][bloqade.builder.coupling.Hyperfine] for more details.
        """
        return Hyperfine(self)
