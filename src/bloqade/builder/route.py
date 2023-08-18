from .start import ProgramStart
from .coupling import LevelCoupling
from .field import Field, Rabi
from .pragmas import Assignable, Parallelizable, Flattenable
from .backend import BackendRoute
from .compile.trait import ParseSequence


class PulseRoute(ProgramStart, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, Parallelizable, Flattenable, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute, ParseSequence):
    pass
