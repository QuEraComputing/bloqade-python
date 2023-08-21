from .start import ProgramStart
from .coupling import LevelCoupling
from .field import Field, Rabi
from .pragmas import Assignable, Parallelizable, Flattenable
from .backend import BackendRoute


class PulseRoute(ProgramStart, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, Parallelizable, Flattenable, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
