from typing import List
from .base import Builder
from .start import ProgramStart
from .coupling import LevelCoupling
from .field import Field, Rabi
from .assign import Assignable
from .parallelize import Parallelizable
from .backend.quera import QuEra
from .backend.braket import Braket


class PulseRoute(ProgramStart, LevelCoupling, Field, Rabi):
    pass


class BackendRoute(QuEra, Braket):
    pass


class PragmaRoute(Assignable, Parallelizable, BackendRoute):
    pass


class Flatten(PragmaRoute):
    def __init__(self, orders: List[str], parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._orders = orders
