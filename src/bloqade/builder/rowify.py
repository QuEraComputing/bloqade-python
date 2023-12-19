from beartype.typing import Optional
from bloqade.builder.base import Builder
from bloqade.builder.backend import BackendRoute
from bloqade.builder.typing import LiteralType


class Rowify(BackendRoute, Builder):
    def __init__(
        self,
        row_constraint: Optional[LiteralType],
        radial_constraint: Optional[LiteralType],
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._row_constraint = row_constraint
        self._radial_constraint = radial_constraint
