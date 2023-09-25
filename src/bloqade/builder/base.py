from typing import Optional, Union, List
from numbers import Real

from bloqade.builder.parse.trait import CompileJSON, Parse

ParamType = Union[Real, List[Real]]


class Builder(CompileJSON, Parse):
    __match_args__ = ("__parent__",)

    def __init__(
        self,
        parent: Optional["Builder"] = None,
    ) -> None:
        self.__parent__ = parent

    # def _repr_pretty_(self, p, cycle):
    #     from bloqade.ir.tree_print import Printer

    #     Printer(p).print(self.parse_circuit(), cycle)

    # def __str__(self) -> str:
    #     return self.parse_circuit().__str__()
