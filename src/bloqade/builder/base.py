from typing import Optional, Union, List
from numbers import Real

from .compile.trait import CompileJSON, ParseRegister

ParamType = Union[Real, List[Real]]


class Builder(CompileJSON, ParseRegister):
    __match_args__ = ("__parent__",)

    def __init__(
        self,
        parent: Optional["Builder"] = None,
    ) -> None:
        self.__parent__ = parent
