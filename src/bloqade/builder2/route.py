from .start import ProgramStart
from .coupling import LevelCoupling
from .field import Field, Rabi
from .assign import Assignable
from .parallelize import Parallelizable
from .backend import BackendRoute
from .flatten import Flattenable


class PulseRoute(ProgramStart, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, Parallelizable, BackendRoute):
    pass


class WaveformRoute(PulseRoute, Flattenable, PragmaRoute):
    pass
    # def flatten(self, orders: List[str]) -> "Flatten":
    #     return Flatten(orders, self)


# class Flatten(Parallelizable, BackendRoute):
#     def __init__(self, orders: List[str], parent: Builder | None = None) -> None:
#         super().__init__(parent)
#         self._orders = orders
