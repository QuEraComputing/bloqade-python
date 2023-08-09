from .base import Builder
from .parallelize import Parallelize
from .assign import AssignBase, Assign
from .flatten import Flatten
from typing import Any, List


class Flattenable(Builder):
    def flatten(self, orders: List[str]) -> Flatten:
        return Flatten(orders, self)


class Parallelizable(Builder):
    def parallelize(self, cluster_spacing: Any) -> Parallelize:
        return Parallelize(cluster_spacing, self)


class Assignable(AssignBase):
    def assign(self, **assignments) -> Assign:
        return Assign(parent=self, **assignments)
