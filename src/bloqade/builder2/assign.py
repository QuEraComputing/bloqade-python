from typing import Optional
from .base import Builder


class Assignable(Builder):
    def assign(self, **assignments) -> "Assign":
        return Assign(parent=self, **assignments)

    def batch_assign(self, **assignments) -> "BatchAssign":
        return BatchAssign(parent=self, **assignments)


class AssignBase(Assignable):
    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        super().__init__(parent)
        self._assignments = assignments


class Assign(AssignBase):
    pass


class BatchAssign(AssignBase):
    pass
