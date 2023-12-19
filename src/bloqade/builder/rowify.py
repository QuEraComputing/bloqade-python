from beartype.typing import Optional
from bloqade.builder.base import Builder
from bloqade.builder.backend import BackendRoute
from bloqade.builder.pragmas import Parallelizable


class Rowify(BackendRoute, Parallelizable, Builder):
    def __init__(self, parent: Optional[Builder] = None) -> None:
        super().__init__(parent)
