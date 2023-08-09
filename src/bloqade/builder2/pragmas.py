from .base import Builder
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .parallelize import Parallelize
    from .assign import Assign
    from .flatten import Flatten


class Flattenable(Builder):
    def flatten(self, orders: List[str]) -> "Flatten":
        from .flatten import Flatten

        return Flatten(orders, self)


class Parallelizable(Builder):
    def parallelize(self, cluster_spacing: Any) -> "Parallelize":
        from .parallelize import Parallelize

        return Parallelize(cluster_spacing, self)


class Assignable(Builder):
    def assign(self, **assignments) -> "Assign":
        from .assign import Assign

        return Assign(parent=self, **assignments)
