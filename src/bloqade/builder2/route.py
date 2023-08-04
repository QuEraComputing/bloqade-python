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
