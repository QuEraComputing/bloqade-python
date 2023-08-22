from .base import Builder
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .parallelize import Parallelize, ParallelizeFlatten
    from .assign import Assign, BatchAssign
    from .flatten import Flatten


class Flattenable(Builder):
    def flatten(self, orders: List[str]) -> "Flatten":
        from .flatten import Flatten

        return Flatten(orders, self)


class Assignable(Builder):
    def assign(self, **assignments) -> "Assign":
        from .assign import Assign

        return Assign(parent=self, **assignments)


class BatchAssignable(Builder):
    def batch_assign(self, **assignments) -> "BatchAssign":
        from .assign import BatchAssign

        return BatchAssign(parent=self, **assignments)


class Parallelizable(Builder):
    def parallelize(self, cluster_spacing: Any) -> "Parallelize":
        from .parallelize import Parallelize

        return Parallelize(cluster_spacing, self)


class FlattenParallelizable(Builder):
    def parallelize(self, cluster_spacing: Any) -> "ParallelizeFlatten":
        from .parallelize import Parallelize

        return Parallelize(cluster_spacing, self)
