from typing import List
from .base import Builder
from .pragmas import Parallelizable
from .backend import BackendRoute


class Flatten(Parallelizable, BackendRoute):
    __match_args__ = ("_order", "__parent__")

    def __init__(self, order: List[str], parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._order = tuple(order)
