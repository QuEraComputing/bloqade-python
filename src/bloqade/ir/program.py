from numbers import Real
from bloqade.ir import Sequence
from typing import TYPE_CHECKING, List, Union, Dict, Tuple
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
        static_params: Dict[str, Union[Real, List[Real]]] = {},
        batch_params: List[Dict[str, Union[Real, List[Real]]]] = [{}],
        order: Tuple[str, ...] = (),
    ):
        self._sequence = sequence
        self._register = register
        self._static_params = static_params
        self._batch_params = batch_params
        # order of flattened parameters
        self._order = order

    @property
    def static_params(self) -> Dict[str, Union[Real, List[Real]]]:
        """Get the instances of variables specified by .assign()

        Returns:
            variable and their instances
        """
        return self._static_params

    @property
    def batch_params(self) -> List[Dict[str, Union[Real, List[Real]]]]:
        """Get the instances of variables specified by .batch_assign()

        Returns:
            batch of variable and their instances
        """
        return self._batch_params

    @property
    def order(self):
        return self._order

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

    def parse_args(self, *args) -> Dict[str, Union[Real, List[Real]]]:
        if len(args) != len(self.order):
            raise ValueError(f"Expected {len(self.order)} arguments, got {len(args)}.")

        return dict(zip(self.order, args))

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
        """Interactive visualization of the program

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the program

        Returns:
            Sequence: the sequence of the program.
                See also [`Sequence`][bloqade.ir.control.sequence.Sequence].

        """
        show(self.figure(**assignments))
