from beartype.typing import Optional
from beartype import beartype
from bloqade.builder.typing import LiteralType
from bloqade.builder.base import Builder
from bloqade.builder.backend import BackendRoute
from bloqade.ir import cast


class Parallelize(BackendRoute, Builder):
    __match_args__ = ("_cluster_spacing", "__parent__")

    @beartype
    def __init__(
        self, cluster_spacing: LiteralType, parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._cluster_spacing = cast(cluster_spacing)
