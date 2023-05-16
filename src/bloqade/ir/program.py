from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Union, List
from numbers import Number
from bloqade.location.multiplex import multiplex_register

if TYPE_CHECKING:
    from bloqade.location.base import AtomArrangement


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(
        self,
        register: "AtomArrangement",
        sequence: Sequence,
        assignments: Dict[str, Union[Number, List[Number]]] = {},
        cluster_spacing: Optional[float] = None,
    ):
        self._sequence = sequence
        self._assignments = assignments

        if register is None:
            raise ValueError("AtomArrangement required to construct program")

        if cluster_spacing:
            self._register, self._mapping = multiplex_register(
                register, cluster_spacing
            )
        else:
            self._register = register
            self._mapping = None

    @property
    def register(self):
        return self._register

    @property
    def mapping(self):
        return self._mapping

    @property
    def sequence(self):
        return self._sequence

    @property
    def assignments(self):
        return self._assignments
