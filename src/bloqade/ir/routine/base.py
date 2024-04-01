# from bloqade.ir.routine.params import Params
from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.ir import AtomArrangement, ParallelRegister, Sequence

from bloqade.builder.base import Builder
from bloqade.builder.parse.trait import Parse, Show
from bloqade.ir.routine.params import Params

from pydantic.v1 import ConfigDict
from pydantic.v1.dataclasses import dataclass
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from bloqade.ir.routine.braket import BraketServiceOptions
    from bloqade.ir.routine.quera import QuEraServiceOptions
    from bloqade.ir.routine.bloqade import BloqadeServiceOptions


class RoutineParse(Parse):
    def parse_register(self: "RoutineBase") -> Union[AtomArrangement, ParallelRegister]:
        return self.circuit.register

    def parse_sequence(self: "RoutineBase") -> Sequence:
        return self.circuit.sequence

    def parse_circuit(self: "RoutineBase") -> AnalogCircuit:
        return self.circuit

    def parse(self: "RoutineBase") -> "Routine":
        if self.source is None:
            raise ValueError("Cannot parse a routine without a source Builder.")
        return self


class RoutineShow(Show):
    def show(self: "RoutineBase", *args, batch_index: int = 0):
        """Show an interactive plot of the routine.

        batch_index: int
            which parameter set out of the batch to use. Default is 0.
            If there are no batch parameters, use 0.

        *args: Any
            Specify the parameters that are defined in the `.args([...])` build step.

        """
        if self.source is None:
            raise ValueError("Cannot show a routine without a source Builder.")

        return self.source.show(*args, batch_id=batch_index)


__pydantic_dataclass_config__ = ConfigDict(arbitrary_types_allowed=True)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class RoutineBase(RoutineParse, RoutineShow):
    source: Optional[Builder]
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
