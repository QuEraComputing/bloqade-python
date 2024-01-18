from bloqade.builder.drive import Drive
from bloqade.builder.coupling import LevelCoupling
from bloqade.builder.field import Field, Rabi
from bloqade.builder.pragmas import (
    Assignable,
    BatchAssignable,
    Parallelizable,
    AddArgs,
)
from bloqade.builder.backend import BackendRoute


class PulseRoute(Drive, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, BatchAssignable, Parallelizable, AddArgs, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
