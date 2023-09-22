from beartype import beartype
from beartype.typing import List, Optional, Union
from bloqade.ir.scalar import Variable
from bloqade.builder.base import Builder
from bloqade.builder.pragmas import Parallelizable
from bloqade.builder.backend import BackendRoute


class Flatten(Parallelizable, BackendRoute, Builder):
    __match_args__ = ("_order", "__parent__")

    @beartype
    def __init__(
        self, order: List[Union[str, Variable]], parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._order = tuple([o.name if isinstance(o, Variable) else o for o in order])
