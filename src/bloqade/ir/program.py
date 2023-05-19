from bloqade.ir import Sequence
from bloqade.ir.location.base import AtomArrangement


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(
        self,
        register: AtomArrangement,
        sequence: Sequence,
    ):
        self._sequence = sequence
        self._register = register

    @property
    def register(self):
        return self._register

    @property
    def sequence(self):
        return self._sequence
