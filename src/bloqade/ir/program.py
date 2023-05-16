from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Union, List
from numbers import Number

if TYPE_CHECKING:
    from bloqade.atoms.base import AtomArrangement


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(
        self,
        register: Optional["AtomArrangement"],
        sequence: Sequence,
        assignments: Optional[Dict[str, Union[Number, List[Number]]]] = None,
    ):
        self._register = register
        self._sequence = sequence
        self._assignments = assignments

    @property
    def register(self):
        return self._register

    @property
    def sequence(self):
        return self._sequence

    @property
    def assignments(self):
        return self._assignments
