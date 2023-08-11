from typing import Optional, Any
from .base import Builder
from .backend import SubmitBackendRoute


class Parallelize(SubmitBackendRoute):
    __match_args__ = ("_cluster_spacing", "__parent__")

    def __init__(self, cluster_spacing: Any, parent: Optional[Builder] = None) -> None:
        super().__init__(parent)
        self._cluster_spacing = cluster_spacing
