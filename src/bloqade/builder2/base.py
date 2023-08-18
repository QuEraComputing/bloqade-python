from typing import Optional
from .compile.trait import CompileJSON, ParseRegister


class Builder(CompileJSON, ParseRegister):
    __match_args__ = ("__parent__",)

    def __init__(
        self,
        parent: Optional["Builder"] = None,
    ) -> None:
        self.__parent__ = parent
