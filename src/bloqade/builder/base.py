from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from bloqade.ir.location.base import AtomArrangement, ParallelRegister


class Builder:
    def __init__(
        self,
        parent: Optional["Builder"] = None,
        register: Optional[Union["AtomArrangement", "ParallelRegister"]] = None,
    ) -> None:
        self.__parent__ = parent
        self.__register__ = register
