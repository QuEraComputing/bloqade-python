from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Union, List
from numbers import Number
from bloqade.lattice.multiplex import multiplex_lattice

if TYPE_CHECKING:
    from bloqade.lattice.base import Lattice


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(
        self,
        lattice: "Lattice",
        sequence: Sequence,
        assignments: Dict[str, Union[Number, List[Number]]] = {},
        cluster_spacing: Optional[float] = None,
    ):
        self._sequence = sequence
        self._assignments = assignments

        if lattice is None:
            raise ValueError("Lattice required to construct program")

        if cluster_spacing:
            self._lattice, self._mapping = multiplex_lattice(lattice, cluster_spacing)
        else:
            self._lattice = lattice
            self._mapping = None

    @property
    def lattice(self):
        return self._lattice

    @property
    def mapping(self):
        return self._mapping

    @property
    def sequence(self):
        return self._sequence

    @property
    def assignments(self):
        return self._assignments
