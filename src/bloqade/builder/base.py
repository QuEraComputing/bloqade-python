from typing import Optional
from .compile.trait import CompileJSON, CompileRegister


class Builder(CompileJSON, CompileRegister):
    __match_args__ = ("__parent__",)

    def __init__(
        self,
        parent: Optional["Builder"] = None,
    ) -> None:
        self.__parent__ = parent
