# from bloqade.core.ir.routine.params import Params
from bloqade.core.ir.analog_circuit import AnalogCircuit
from bloqade.core.ir import AtomArrangement, ParallelRegister, Sequence

from bloqade.core.builder.base import Builder
from bloqade.core.builder.parse.trait import Parse, Show
from bloqade.core.ir.routine.params import Params

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from bloqade.core.ir.routine.braket import BraketServiceOptions
    from bloqade.core.ir.routine.quera import QuEraServiceOptions
    from bloqade.core.ir.routine.bloqade import BloqadeServiceOptions


class RoutineParse(Parse):
    def parse_register(self: "RoutineBase") -> Union[AtomArrangement, ParallelRegister]:
        """Return the register associated with this program."""
        return self.circuit.register

    def parse_sequence(self: "RoutineBase") -> Sequence:
        """Return the pulse sequence associated with this program."""
        return self.circuit.sequence

    def parse_circuit(self: "RoutineBase") -> AnalogCircuit:
        """Return the circuit associated with this program."""
        return self.circuit

    def parse(self: "RoutineBase") -> "Routine":
        """Return the routine associated with this program."""
        return self


class RoutineShow(Show):
    def show(self: "RoutineBase", batch_index: int = 0):
        return self.source.show(batch_index)


__pydantic_dataclass_config__ = ConfigDict(arbitrary_types_allowed=True)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class RoutineBase(RoutineParse, RoutineShow):
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
