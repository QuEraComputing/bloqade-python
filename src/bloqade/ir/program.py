from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Union, List
from numbers import Number

if TYPE_CHECKING:
    from bloqade.lattice.base import Lattice


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(
        self,
        lattice: Optional["Lattice"],
        sequence: Sequence,
        assignments: Optional[Dict[str, Union[Number, List[Number]]]] = None,
    ):
        self._lattice = lattice
        self._sequence = sequence
        self._assignments = assignments

    @property
    def lattice(self):
        return self._lattice

    @property
    def sequence(self):
        return self._sequence

    @property
    def assignments(self):
        return self._assignments
