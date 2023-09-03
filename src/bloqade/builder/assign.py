from typing import Optional, Union, List
from bloqade.builder.base import Builder
from bloqade.builder.pragmas import Parallelizable, Flattenable, BatchAssignable
from bloqade.builder.backend import BackendRoute
from bloqade.builder.parse.trait import Parse
import numpy as np
from numbers import Real
from decimal import Decimal


def cast_param(value: Union[Real, List[Real]]):
    if isinstance(value, list):
        return list(map(Decimal, map(str, value)))

    if isinstance(value, (Real, Decimal)):
        return Decimal(str(value))

    raise ValueError("value must be a real number or a list of real numbers")


class AssignBase(Builder):
    __match_args__ = ("_assignments", "__parent__")

    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        super().__init__(parent)
        # TODO: implement checks for assignments
        self._assignments = assignments


class Assign(
    AssignBase, BatchAssignable, Flattenable, Parallelizable, BackendRoute, Parse
):
    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        for key, value in assignments.items():
            assignments[key] = cast_param(value)
        super().__init__(parent, **assignments)


class BatchAssign(AssignBase, Parallelizable, BackendRoute, Parse):
    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        if not len(np.unique(list(map(len, assignments.values())))) == 1:
            raise ValueError(
                "all the assignment variables need to have same number of elements."
            )

        for key, values in assignments.items():
            assignments[key] = list(map(cast_param, values))

        super().__init__(parent, **assignments)
