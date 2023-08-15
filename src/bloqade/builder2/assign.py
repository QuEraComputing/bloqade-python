from typing import Optional
from .base import Builder
from .pragmas import Parallelizable, Flattenable
from .backend import SubmitBackendRoute
from .compile.trait import CompileProgram


class AssignBase(Builder):
    __match_args__ = ("_assignments", "__parent__")

    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        super().__init__(parent)
        self._assignments = assignments


class Assign(
    AssignBase, Flattenable, Parallelizable, SubmitBackendRoute, CompileProgram
):
    def batch_assign(self, **assignments) -> "BatchAssign":
        return BatchAssign(parent=self, **assignments)


class BatchAssign(AssignBase, Parallelizable, SubmitBackendRoute, CompileProgram):
    pass
