from typing import Optional
from .base import Builder
from .pragmas import Parallelizable, Flattenable, BatchAssignable
from .backend import BackendRoute
from .compile.trait import Parse
import numpy as np


class AssignBase(Builder):
    __match_args__ = ("_assignments", "__parent__")

    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        super().__init__(parent)
        # TODO: implement checks for assignments
        self._assignments = assignments


class Assign(
    AssignBase, BatchAssignable, Flattenable, Parallelizable, BackendRoute, Parse
):
    pass


class BatchAssign(AssignBase, Parallelizable, BackendRoute, Parse):
    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        super().__init__(parent, **assignments)
        if not len(np.unique(list(map(len, assignments.values())))) == 1:
            raise ValueError(
                "all the assignment variables need to have same number of elements."
            )
