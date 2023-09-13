from beartype.typing import Optional
from bloqade.builder.typing import ScalarType
from bloqade.builder.base import Builder
from bloqade.builder.backend import BackendRoute
from bloqade.builder.parse.trait import Parse
from bloqade.ir import cast


class Parallelize(BackendRoute, Parse):
    __match_args__ = ("_cluster_spacing", "__parent__")

    def __init__(
        self, cluster_spacing: ScalarType, parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._cluster_spacing = cast(cluster_spacing)
