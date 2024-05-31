from bloqade.builder.base import Builder
from bloqade.builder.field import Rabi, Detuning


class LevelCoupling(Builder):
    @property
    def detuning(self) -> Detuning:
        """
        Specify the [`Detuning`][bloqade.builder.field.Detuning] [`Field`][bloqade.builder.field.Field] of your program.
        You will be able to specify the spatial modulation afterwards.

        Args:
            None

        Returns:
            [`Detuning`][bloqade.builder.field.Detuning]: A program node representing the detuning field.

        Note:
            The detuning specifies how off-resonant the laser being applied to the atoms is from the atomic energy transition, driven by the Rabi frequency.

            Example:
                ```python
                from bloqade import start
                geometry = start.add_position((0,0))
                coupling = geometry.rydberg
                coupling.detuning
                ```

            - Next Possible Steps
            You may continue building your program via:
            - [`uniform`][bloqade.builder.field.Detuning.uniform]: To address all atoms in the field
            - [`location(locations, scales)`][bloqade.builder.field.Detuning.location]: To address atoms at specific
            locations via indices
            - [`scale(coeffs)`][bloqade.builder.field.Detuning.scale]: To address all atoms with an individual scale factor
        """

        return Detuning(self)

    @property
    def rabi(self) -> Rabi:
        """
        Specify the complex-valued [`Rabi`][bloqade.builder.field.Rabi]
        field of your program.

        The Rabi field is composed of a real-valued Amplitude and Phase field.


        Args:
            None

        Returns:
            Rabi: A program node representing the Rabi field.

        Note:
            Next possible steps to build your program are
            creating the RabiAmplitude field and RabiPhase field of the field:
            - `...rabi.amplitude`: To create the Rabi amplitude field
            - `...rabi.phase`: To create the Rabi phase field
        """

        return Rabi(self)


class Rydberg(LevelCoupling):
    """
    This node represents level coupling of the Rydberg state.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.rydberg
        >>> type(node)
        <class 'bloqade.builder.coupling.Rydberg'>

        - Rydberg level coupling has two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

        >>> ryd_detune = bloqade.start.rydberg.detuning
        >>> ryd_rabi = bloqade.start.rydberg.rabi
    """

    def __bloqade_ir__(self):
        """
        Generate the intermediate representation (IR) for the Rydberg level coupling.

        Args:
            None

        Returns:
            IR: An intermediate representation of the Rydberg level coupling sequence.

        Raises:
            None

        Note:
            This method is used internally by the Bloqade framework.
        """
        from bloqade.ir.control.sequence import rydberg

        return rydberg


class Hyperfine(LevelCoupling):
    """
    This node represents level coupling between hyperfine states.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.hyperfine
        >>> type(node)
        <class 'bloqade.builder.coupling.Hyperfine'>

        - Hyperfine level coupling has two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

        >>> hyp_detune = bloqade.start.hyperfine.detuning
        >>> hyp_rabi = bloqade.start.hyperfine.rabi
    """

    def __bloqade_ir__(self):
        """
        Generate the intermediate representation (IR) for the Hyperfine level coupling.

        Args:
            None

        Returns:
            IR: An intermediate representation of the Hyperfine level coupling sequence.

        Raises:
            None

        Note:
            This method is used internally by the Bloqade framework.
        """
        from bloqade.ir.control.sequence import hyperfine

        return hyperfine
