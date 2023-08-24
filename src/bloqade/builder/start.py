from .base import Builder
from bloqade.ir.control.sequence import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sequence_builder import SequenceBuilder


class ProgramStart(Builder):
    """
    ProgramStart is the base class for a starting/entry node for building a program.
    """

    @property
    def rydberg(self):
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
        from .coupling import Rydberg

        return Rydberg(self)

    @property
    def hyperfine(self):
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
        from .coupling import Hyperfine

        return Hyperfine(self)

    def apply(self, sequence: Sequence) -> "SequenceBuilder":
        """apply an existing pulse sequence to the program."""
        from .sequence_builder import SequenceBuilder

        return SequenceBuilder(self, sequence)
