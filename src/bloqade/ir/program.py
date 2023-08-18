from numbers import Real
from bloqade.ir import Sequence
from typing import TYPE_CHECKING, List, Union, Dict, Tuple

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
    def static_params(self):
        return self._static_params

    @property
    def batch_params(self):
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

    def parse_args(self, *args) -> List[Dict[str, Union[Real, List[Real]]]]:
        if len(args) != len(self.order):
            raise ValueError(f"Expected {len(self.order)} arguments, got {len(args)}.")

        base_params = dict(zip(self.order, args))

        params = []
        for param in self.batch_params:
            params.append(base_params | param)

        return params
