from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bloqade.location.base import AtomArrangement


class Builder:
    def __init__(
        self,
        parent: Optional["Builder"] = None,
        register: Optional["AtomArrangement"] = None,
    ) -> None:
        self.__parent__ = parent
        self.__register__ = register
