from typing import Optional, Union, List
from numbers import Real

from bloqade.builder.parse.trait import Parse, Show

ParamType = Union[Real, List[Real]]


class Builder(Parse, Show):
    def __init__(
        self,
        parent: Optional["Builder"] = None,
    ) -> None:
        self.__parent__ = parent

    def __str__(self):
        return str(self.parse())
