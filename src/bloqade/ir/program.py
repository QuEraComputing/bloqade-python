from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from bloqade.ir.location.base import AtomArrangement, ParallelRegister


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    """Program is a dummy type that bundle register and sequence together."""

    def __init__(
        self,
        register: Union["AtomArrangement", "ParallelRegister"],
        sequence: Sequence,
    ):
        self._sequence = sequence
        self._register = register

    @property
    def register(self):
        """Get the register of the program.

        Returns:
            register (Union["AtomArrangement", "ParallelRegister"])

        Note:
            If the program is built with
            [`parallelize()`][bloqade.builder.emit.Emit.parallelize],
            The the register will be a
            [`ParallelRegister`][bloqade.ir.location.base.ParallelRegister].
            Otherwise it will be a
            [`AtomArrangement`][bloqade.ir.location.base.AtomArrangement].
        """
        return self._register

    @property
    def sequence(self):
        """Get the sequence of the program.

        Returns:
            sequence (Sequence)

        """
        return self._sequence
