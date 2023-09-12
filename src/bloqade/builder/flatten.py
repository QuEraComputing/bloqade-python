from typing import List, Optional
from bloqade.builder.base import Builder
from bloqade.builder.backend import BackendRoute


class Flatten(BackendRoute):
    __match_args__ = ("_order", "__parent__")

    def __init__(self, order: List[str], parent: Optional[Builder] = None) -> None:
        super().__init__(parent)
        self._order = tuple(order)
