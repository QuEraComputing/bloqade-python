from typing import Optional, Any
from .base import Builder


class Parallelizable(Builder):
    def parallelize(self, cluster_spacing: Any) -> "Parallelize":
        return Parallelize(cluster_spacing, self)


class Parallelize(Builder):
    def __init__(self, cluster_spacing: Any, parent: Optional[Builder] = None) -> None:
        super().__init__(parent)
        self._cluster_spacing = cluster_spacing
