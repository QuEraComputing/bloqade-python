from bloqade._core.builder.drive import Drive
from bloqade._core.builder.coupling import LevelCoupling
from bloqade._core.builder.field import Field, Rabi
from bloqade._core.builder.pragmas import (
    Assignable,
    BatchAssignable,
    Parallelizable,
    AddArgs,
)
from bloqade._core.builder.backend import BackendRoute


class PulseRoute(Drive, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, BatchAssignable, Parallelizable, AddArgs, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
