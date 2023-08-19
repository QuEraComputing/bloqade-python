from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Union
from bokeh.io import show
from bokeh.layouts import row

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
            Sequence: the sequence of the program.
                See also [`Sequence`][bloqade.ir.control.sequence.Sequence].

        """
        return self._sequence

    def __repr__(self):
        out = ""
        if self._register is not None:
            out += self._register.__repr__()

        out += "\n"

        if self._sequence is not None:
            out += self._sequence.__repr__()

        return out

    def figure(self, **assignments):
        fig_reg = self._register.figure(**assignments)
        fig_seq = self._sequence.figure(**assignments)
        return row(fig_seq, fig_reg)

    def show(self, **assignments):
        show(self.figure(**assignments))
