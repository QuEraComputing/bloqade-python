from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bloqade.lattice.base import Lattice


class Builder:
    def __init__(
        self, parent: Optional["Builder"] = None, lattice: Optional["Lattice"] = None
    ) -> None:
        self.__parent__ = parent
        self.__lattice__ = lattice
