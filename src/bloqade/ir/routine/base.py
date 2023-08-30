# from bloqade.ir.routine.params import Params
from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.ir import AtomArrangement, ParallelRegister, Sequence

from bloqade.builder.base import Builder
from bloqade.ir.routine.params import Params


from dataclasses import dataclass
from typing import TYPE_CHECKING, Union, Tuple

if TYPE_CHECKING:
    from bloqade.ir.routine.braket import BraketServiceOptions
    from bloqade.ir.routine.quera import QuEraServiceOptions


class RoutineParse:
    def parse_register(self: "RoutineBase") -> Union[AtomArrangement, ParallelRegister]:
        return self.source.parse_register()

    def parse_sequence(self: "RoutineBase") -> Sequence:
        return self.source.parse_sequence()

    def parse_circuit(self: "RoutineBase") -> AnalogCircuit:
        return self.source.parse_circuit()

    def parse_source(self: "RoutineBase") -> Tuple[AnalogCircuit, Params]:
        return self.source.parse_source()


@dataclass(frozen=True)
class RoutineBase(RoutineParse):
    source: Builder


@dataclass(frozen=True)
class Routine(RoutineBase):
    """Result of parsing a completed Builder string."""

    @property
    def braket(self) -> "BraketServiceOptions":
        from .braket import BraketServiceOptions

        return BraketServiceOptions(source=self.source)

    @property
    def quera(self) -> "QuEraServiceOptions":
        from .quera import QuEraServiceOptions

        return QuEraServiceOptions(source=self.source)
