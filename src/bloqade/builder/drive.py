from bloqade.builder.coupling import Rydberg, Hyperfine


class Drive:
    @property
    def rydberg(self) -> Rydberg:
        """
        - Address the Rydberg level coupling in your program.
        - Next possible steps to build your program are specifying the [`Rabi`][bloqade.builder.field.Rabi] field or [`Detuning`][bloqade.builder.field.Detuning] field.
            - |_ `...rydberg.rabi`: for Rabi field
            - |_ `...rydberg.detuning`: for Detuning field
        - In the absence of a field you the value is set to zero by default.

        Example Usage:
        ```
        >>> target_rydberg_rabi = start.rydberg.rabi
        >>> type(target_rydberg_rabi)
        bloqade.builder.field.Rabi

        >>> targe_hyperfine_rabi = start.rydberg.detuning
        >>> type(target_rydberg_detuning)
        bloqade.builder.field.Detuning
        ```
        """
        return Rydberg(self)

    @property
    def hyperfine(self) -> Hyperfine:
        """
        - Address the Hyperfine level coupling in your program.
        - Next possible steps to build your program are specifying the [`Rabi`][bloqade.builder.field.Rabi] field or [`Detuning`][bloqade.builder.field.Detuning] field.
            - |_ `...hyperfine.rabi`: for Rabi field
            - |_ `...hyperfine.detuning`: for Detuning field
        - In the absence of a field you the value is set to zero by default.

        Example Usage:
        ```
        >>> target_hyperfine_rabi = start.hyperfine.rabi
        >>> type(target_rydberg_rabi)
        bloqade.builder.field.Rabi

        >>> targe_hyperfine_detuning = start.hyperfine.detuning
        >>> type(target_hyperfine_detuning)
        bloqade.builder.field.Detuning
        ```
        """
        return Hyperfine(self)
