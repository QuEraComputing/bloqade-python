from typing import Optional, Any
from .base import Builder
from .backend import SubmitBackendRoute


class Parallelize(Builder, SubmitBackendRoute):
    def __init__(self, cluster_spacing: Any, parent: Optional[Builder] = None) -> None:
        super().__init__(parent)
        self._cluster_spacing = cluster_spacing
