from bloqade.builder.base import Builder
from bloqade.builder.field import Rabi, Detuning


class LevelCoupling(Builder):
    @property
    def detuning(self) -> Detuning: # field is summation of one or more drives, waveform + spatial modulation = drive
        """
        - Specify the [`Detuning`][bloqade.builder.field.Detuning] [`Field`][bloqade.builder.Field] of your program.
        - A "field" is a summation of one or more "drives", with a drive being the sum of a waveform and spatial modulation.
            - You are currently building the spatial modulation component and will be able to specify a waveform
        - You can do this by:
            - |_ `...detuning.uniform`: To address all atoms in the field
            - |_ `...detuning.location(int)`: To address an atom at a specific location via index
            - |_ `...detuning.var(str)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by specifying a single variable and then assigning it a list of coordinates
        
        Usage Examples:
        ```
        >>> prog = start.add_position(([(0,0), (1,2)]).rydberg.detuning
        # subsequent specified waveform will target all atoms equally
        >>> prog.uniform
        # target individual atoms via index in the list of coordinates you passed in earlier
        # (This is chainable)
        >>> prog.location(0).location(1)
        # target individual atoms via index represented as a variable
        # (This is NOT chainable)
        >>> prog.var("atom_1")
        # target MULTIPLE atoms via indices represented as a single variable
        # where ... is the rest of your program as you cannot perform variable
        # assignment afterwards
        >>> prog.var("locations")...assign(locations = [0, 1])
        ```
        """

        return Detuning(self)

    @property
    def rabi(self) -> Rabi:
        """
        - Specify the complex-valued [`Rabi`][bloqade.builder.field.Rabi] field of your program.
        - The Rabi field is composed of a real-valued Amplitude and Phase field
        - Next possible steps to build your program are 
          creating the [`RabiAmplitude`][bloqade.builder.field.RabiAmplitude] field and [`RabiPhase`][bloqade.builder.field.RabiAmplitude] field of the field:
            - |_ `...rabi.amplitude`: To create the Rabi amplitude field
            - |_ `...rabi.phase`: To create the Rabi phase field

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
