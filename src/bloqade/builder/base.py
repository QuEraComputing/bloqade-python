from typing import TYPE_CHECKING, Optional, Union
from bloqade.ir.control.pulse import FieldName
from pydantic import BaseModel


if TYPE_CHECKING:
    from bloqade.ir.location.base import AtomArrangement, ParallelRegister


class BuildCache(BaseModel):
    field_name: Optional[FieldName] = None


class Builder:
    def __init__(
        self,
        parent: Optional["Builder"] = None,
        register: Optional[Union["ParallelRegister", "AtomArrangement"]] = None,
    ) -> None:
        self.__parent__ = parent

        if self.__parent__ is not None:
            self.__build_cache__ = BuildCache(**self.__parent__.__build_cache__.dict())
            self.__register__ = self.__parent__.__register__
        else:
            self.__register__ = register
            self.__build_cache__ = BuildCache()
