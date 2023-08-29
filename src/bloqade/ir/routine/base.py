# from bloqade.ir.routine.params import Params
# from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.builder.base import Builder
from bloqade.ir.routine.braket import BraketServiceOptions
from dataclasses import dataclass


@dataclass(frozen=True)
class Routine:
    """Result of parsing a completed Builder string."""

    source: Builder
    # circuit: AnalogCircuit
    # params: Params

    @property
    def braket(self) -> BraketServiceOptions:
        return BraketServiceOptions(parent=self)
