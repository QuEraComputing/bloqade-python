from beartype.typing import Optional
from beartype import beartype
from bloqade.builder.typing import LiteralType
from bloqade.builder.base import Builder
from bloqade.builder.backend import BackendRoute
from bloqade.builder.pragmas import RowCoarsable
from bloqade.ir import cast


class Parallelize(BackendRoute, RowCoarsable, Builder):
    @beartype
    def __init__(
        self, cluster_spacing: LiteralType, parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._cluster_spacing = cast(cluster_spacing)
