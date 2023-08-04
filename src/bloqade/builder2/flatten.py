from typing import List
from .base import Builder
from .parallelize import Parallelizable
from .backend import BackendRoute


class Flattenable(Builder):
    def flatten(self, orders: List[str]) -> "Flatten":
        return Flatten(orders, self)


class Flatten(Parallelizable, BackendRoute):
    def __init__(self, orders: List[str], parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._orders = orders
