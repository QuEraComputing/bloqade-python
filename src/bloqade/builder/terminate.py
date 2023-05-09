from .spatial import SpatialModulation
from .coupling import LevelCoupling
from .field import Rabi
from .start import ProgramStart
from .emit import Emit


class Terminate(SpatialModulation, LevelCoupling, Rabi, ProgramStart, Emit):
    pass
