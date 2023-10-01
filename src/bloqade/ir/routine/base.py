# from bloqade.ir.routine.params import Params
from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.ir import AtomArrangement, ParallelRegister, Sequence

from bloqade.builder.base import Builder
from bloqade.ir.routine.params import Params

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from bloqade.ir.routine.braket import BraketServiceOptions
    from bloqade.ir.routine.quera import QuEraServiceOptions
    from bloqade.ir.routine.bloqade import BloqadeServiceOptions


class RoutineParse:
    def parse_register(self: "RoutineBase") -> Union[AtomArrangement, ParallelRegister]:
        return self.circuit.register

    def parse_sequence(self: "RoutineBase") -> Sequence:
        return self.circuit.sequence

    def parse_circuit(self: "RoutineBase") -> AnalogCircuit:
        return self.circuit

    def parse(self: "RoutineBase") -> "Routine":
        return self


__pydantic_dataclass_config__ = ConfigDict(arbitrary_types_allowed=True)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class RoutineBase(RoutineParse):
    source: Builder
    circuit: AnalogCircuit
    params: Params

    def __str__(self):
        out = self.__class__.__name__ + "\n"
        out = out + str(self.circuit)
        out = out + "\n---------------------\n"
        out = out + str(self.params)
        return out


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class Routine(RoutineBase):
    """Result of parsing a completed Builder string."""

    @property
    def braket(self) -> "BraketServiceOptions":
        from .braket import BraketServiceOptions

        return BraketServiceOptions(self.source, self.circuit, self.params)

    @property
    def quera(self) -> "QuEraServiceOptions":
        from .quera import QuEraServiceOptions

        return QuEraServiceOptions(self.source, self.circuit, self.params)

    @property
    def bloqade(self) -> "BloqadeServiceOptions":
        from .bloqade import BloqadeServiceOptions

        return BloqadeServiceOptions(self.source, self.circuit, self.params)
