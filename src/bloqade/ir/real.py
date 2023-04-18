from dataclasses import dataclass


class Real:
    pass


@dataclass(frozen=True)
class Litreal(Real):
    value: float


@dataclass(frozen=True)
class Variable(Real):
    name: str  # TODO: use a token so we have O(1) comparision
