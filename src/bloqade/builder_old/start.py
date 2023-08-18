from .base import Builder
from .coupling import Rydberg, Hyperfine
import bloqade.ir.control.sequence as SequenceExpr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .emit import Emit


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
        return Hyperfine(self)

    def apply(self, sequence: SequenceExpr) -> "Emit":
        """apply an existing pulse sequence to the program."""
        from .emit import Emit

        if getattr(self, "__sequence__", None) is not None:
            raise NotImplementedError("Cannot apply multiple sequences")

        return Emit(self, register=self.__register__, sequence=sequence)
