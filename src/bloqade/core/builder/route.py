from bloqade.core.builder.drive import Drive
from bloqade.core.builder.coupling import LevelCoupling
from bloqade.core.builder.field import Field, Rabi
from bloqade.core.builder.pragmas import (
    Assignable,
    BatchAssignable,
    Parallelizable,
    AddArgs,
)
from bloqade.core.builder.backend import BackendRoute


class PulseRoute(Drive, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, BatchAssignable, Parallelizable, AddArgs, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
