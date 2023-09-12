from typing import Optional, Any
from bloqade.builder.base import Builder
from bloqade.builder.backend import BackendRoute
from bloqade.builder.parse.trait import Parse
from bloqade.ir import cast


class ParallelizeBase(Builder):
    __match_args__ = ("_cluster_spacing", "__parent__")

    def __init__(self, cluster_spacing: Any, parent: Optional[Builder] = None) -> None:
        super().__init__(parent)
        self._cluster_spacing = cast(cluster_spacing)


# the idea here is that parallelize in different parts of the builder
# will lead to different backends depending on the order of the calls


# If parallize before calling flatten restrict the API to only use the
# SubmitBackendRoute
class Parallelize(ParallelizeBase, BackendRoute, Parse):
    pass
