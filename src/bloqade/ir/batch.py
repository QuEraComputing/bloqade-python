import dataclasses
from typing import Dict, OrderedDict
from decimal import Decimal
from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.ir.program import BloqadeProgram


@dataclasses.dataclass
class BloqadeTask:
    """Result of assigning a particular batch parameters in Params to a BloqadeAST."""

    ast: AnalogCircuit  # further assign params
    assingments: Dict[str, Decimal]  # store assigned params


@dataclasses.dataclass
class BloqadeBatch:
    """Result of assigning all Params to a BloqadeAST."""

    program: BloqadeProgram
    tasks: OrderedDict[int, BloqadeTask]
