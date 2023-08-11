from typing import Optional
from typing import Any
import json


class Builder:
    __match_args__ = ("__parent__",)

    def __init__(
        self,
        parent: Optional["Builder"] = None,
    ) -> None:
        self.__parent__ = parent


class DefaultBuilderEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> dict:
        match obj:
            case Builder(None):
                return {"type": obj.__class__.__name__}
            case Builder(parent):
                return {
                    "type": obj.__class__.__name__,
                    "parent": self.default(parent),
                }
            case _:
                return super().default(obj)
