from typing import Optional


class Builder:
    def __init__(self, parent: Optional["Builder"] = None) -> None:
        self.__parent__ = parent
