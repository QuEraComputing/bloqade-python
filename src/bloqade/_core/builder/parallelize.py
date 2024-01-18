from beartype.typing import Optional
from beartype import beartype
from bloqade._core.builder.typing import LiteralType
from bloqade._core.builder.base import Builder
from bloqade._core.builder.backend import BackendRoute
from bloqade._core.ir import cast


class Parallelize(BackendRoute, Builder):
    @beartype
    def __init__(
        self, cluster_spacing: LiteralType, parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._cluster_spacing = cast(cluster_spacing)
