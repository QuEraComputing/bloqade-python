import pydantic
import dataclasses

from typing import Union, List, Tuple, Dict
from decimal import Decimal
from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.builder.base import Builder

ParamType = Union[Decimal, List[Decimal]]


@pydantic.dataclasses.dataclass(frozen=True)
class Params:
    batch_params: List[Dict[str, ParamType]]
    flatten_params: Tuple[str, ...]

    def parse_args(self, *args) -> Dict[str, Decimal]:
        if len(args) != len(self.flatten_params):
            raise ValueError(
                f"Expected {len(self.flatten_params)} arguments, got {len(args)}."
            )

        args = tuple(map(Decimal, map(str, args)))
        return dict(zip(self.flatten_params, args))

    def batch_assignments(self, *args):
        return [{**self.parse_args(*args), **batch} for batch in self.batch_params]


@dataclasses.dataclass
class BloqadeProgram:
    """Result of parsing a completed Builder string."""

    build: Builder
    circuit: AnalogCircuit
    assignments: Dict[str, ParamType]  # store assigned params
    params: Params  # remaining params to be filled in
