from beartype.typing import Optional
from beartype import beartype
from bloqade.core.builder.typing import LiteralType
from bloqade.core.builder.base import Builder
from bloqade.core.builder.backend import BackendRoute
from bloqade.core.ir import cast


class Parallelize(BackendRoute, Builder):
    @beartype
    def __init__(
        self, cluster_spacing: LiteralType, parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._cluster_spacing = cast(cluster_spacing)
