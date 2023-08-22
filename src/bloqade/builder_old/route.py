from .spatial import SpatialModulation
from .coupling import LevelCoupling
from .field import Rabi
from .start import ProgramStart
from .assign import Assign, BatchAssign


class PulseRoute(SpatialModulation, LevelCoupling, Rabi, ProgramStart):
    pass


class Route(PulseRoute, Assign, BatchAssign):
    pass
