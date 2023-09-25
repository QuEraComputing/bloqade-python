from bloqade.builder.base import Builder
from bloqade.builder.field import Rabi, Detuning


class LevelCoupling(Builder):
    @property
    def detuning(self) -> Detuning:
        """
        - Specify the [`Detuning`][bloqade.builder.field.Detuning] field of your program.
        - Next possible steps to build your program are allowing the field to target specific atoms:
            - |_ `...detuning.uniform`: To address all atoms in the field
            - |_ `...detuning.location(int)`: To address an atom at a specific location via index
            - |_ `...detuning.var(str)`: To address an atom at a specific location via variable name
        
        Usage Examples:
        ```
        >>> prog = start.add_position(([(0,0), (1,2)]).rydberg.detuning
        # target all atoms with waveforms specified later
        >>> prog.uniform
        # target individual atoms via index in the list of coordinates you passed in earlier
        # (This is chainable)
        >>> prog.location(0).location(1)
        # target individual atoms via index represented as a variable
        # (This is also chainable)
        >>> prog.var("atom_1").var("atom_2")
        ```
        """

        return Detuning(self)

    @property
    def rabi(self) -> Rabi:
        """
        - Specify the [`Rabi`][bloqade.builder.field.Rabi] field of your program.
        - Next possible steps to build your program are 
          addressing the [`RabiAmplitude`][bloqade.builder.field.RabiAmplitude] and [`RabiPhase`][] of the field:
            - |_ `...rabi.amplitude`: To address the Rabi amplitude
            - |_ `...rabi.phase`: To address the Rabi phase

        Usage Examples
        ```
        >>> target_rabi_amplitude = start.rydberg.rabi.amplitude
        >>> type(target_rabi_amplitude)
        bloqade.builder.field.RabiAmplitude
        >>> target_rabi_phase = start.rydberg.rabi.phase
        >>> type(target_rabi_phase)
        bloqade.builder.field.RabiPhase
        ```
        """

        return Rabi(self)


class Rydberg(LevelCoupling):
    """
    This node represent level coupling of rydberg state.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.rydberg
        >>> type(node)
        <class 'bloqade.builder.coupling.Rydberg'>

        - Rydberg level coupling have two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

        >>> ryd_detune = bloqade.start.rydberg.detuning
        >>> ryd_rabi = bloqade.start.rydberg.rabi

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.sequence import rydberg

        return rydberg


class Hyperfine(LevelCoupling):
    """
    This node represent level coupling between hyperfine state.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.hyperfine
        >>> type(node)
        <class 'bloqade.builder.coupling.Hyperfine'>

        - Hyperfine level coupling have two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

        >>> hyp_detune = bloqade.start.hyperfine.detuning
        >>> hyp_rabi = bloqade.start.hyperfine.rabi

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.sequence import hyperfine

        return hyperfine
