from bloqade._core.builder.base import Builder
from bloqade._core.builder.field import Rabi, Detuning


class LevelCoupling(Builder):
    @property
    def detuning(
        self,
    ) -> Detuning:  # field is summation of one or more drives,
        # waveform + spatial modulation = drive
        """
        Specify the [`Detuning`][bloqade._core.builder.field.Detuning]
         [`Field`][bloqade._core.builder.Field] of your program.

        A "field" is a summation of one or more "drives", with a drive being the sum
        of a waveform and spatial modulation.

        You are currently building the spatial modulation component and will be
        able to specify a waveform.

        - You can do this by:
            - `...detuning.uniform`: To address all atoms in the field
            - `...detuning.location(locations, scales)`: To address atoms at specific
                locations via indices
            - `...detuning.scale(coeffs)`
                - To address all atoms with an individual scale factor

        """

        return Detuning(self)

    @property
    def rabi(self) -> Rabi:
        """
        Specify the complex-valued [`Rabi`][bloqade._core.builder.field.Rabi]
        field of your program.

        The Rabi field is composed of a real-valued Amplitude and Phase field.

        - Next possible steps to build your program are
          creating the [`RabiAmplitude`][bloqade._core.builder.field.RabiAmplitude] field
          and [`RabiPhase`][bloqade._core.builder.field.RabiAmplitude] field of the field:
            - `...rabi.amplitude`: To create the Rabi amplitude field
            - `...rabi.phase`: To create the Rabi phase field

        """

        return Rabi(self)


class Rydberg(LevelCoupling):
    """
    This node represent level coupling of rydberg state.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.rydberg
        >>> type(node)
        <class 'bloqade._core.builder.coupling.Rydberg'>

        - Rydberg level coupling have two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade._core.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade._core.builder.field.Rabi])

        >>> ryd_detune = bloqade.start.rydberg.detuning
        >>> ryd_rabi = bloqade.start.rydberg.rabi

    """

    def __bloqade_ir__(self):
        from bloqade._core.ir.control.sequence import rydberg

        return rydberg


class Hyperfine(LevelCoupling):
    """
    This node represent level coupling between hyperfine state.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.hyperfine
        >>> type(node)
        <class 'bloqade._core.builder.coupling.Hyperfine'>

        - Hyperfine level coupling have two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade._core.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade._core.builder.field.Rabi])

        >>> hyp_detune = bloqade.start.hyperfine.detuning
        >>> hyp_rabi = bloqade.start.hyperfine.rabi

    """

    def __bloqade_ir__(self):
        from bloqade._core.ir.control.sequence import hyperfine

        return hyperfine
