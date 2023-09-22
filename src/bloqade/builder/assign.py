from itertools import repeat, starmap
from beartype.typing import Optional, List
from bloqade.builder.typing import ParamType
from bloqade.builder.base import Builder
from bloqade.builder.pragmas import Parallelizable, Flattenable, BatchAssignable
from bloqade.builder.backend import BackendRoute
from bloqade.builder.parse.trait import Parse
from numbers import Real
from decimal import Decimal
import numpy as np


def cast_scalar_param(value: ParamType, name: str) -> Decimal:
    if isinstance(value, (Real, Decimal)):
        return Decimal(str(value))

    raise TypeError(
        f"assign parameter '{name}' must be a real number, "
        f"found type: {type(value)}"
    )


def cast_vector_param(value: List[ParamType], name: str) -> List[Decimal]:
    if isinstance(value, np.ndarray):
        value = value.tolist()

    if isinstance(value, (list, tuple)):
        return list(starmap(cast_scalar_param, zip(value, repeat(name))))

    raise TypeError(
        f"assign parameter '{name}' must be a list of real numbers, "
        f"found type: {type(value)}"
    )


def cast_batch_scalar_param(value: List[ParamType], name: str) -> List[Decimal]:
    if isinstance(value, np.ndarray):
        value = value.tolist()

    if isinstance(value, (list, tuple)):
        return list(starmap(cast_scalar_param, zip(value, repeat(name))))

    raise TypeError(
        f"batch_assign parameter '{name}' must be a list of real numbers, "
        f"found type: {type(value)}"
    )


def cast_batch_vector_param(value: List[ParamType], name: str) -> List[List[Decimal]]:
    if isinstance(value, (list, tuple)):
        return list(starmap(cast_vector_param, zip(value, repeat(name))))

    raise TypeError(
        f"batch_assign parameter '{name}' must be a list of lists of real numbers, "
        f"found type: {type(value)}"
    )


class AssignBase(Builder):
    pass


class Assign(
    AssignBase, BatchAssignable, Flattenable, Parallelizable, BackendRoute, Parse
):
    __match_args__ = ("_assignments", "__parent__")

    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        from bloqade.codegen.common.scan_variables import ScanVariablesAnalogCircuit

        super().__init__(parent)

        circuit = self.parse_circuit()
        vars = ScanVariablesAnalogCircuit().emit(circuit)

        self._assignments = {}
        for name, value in assignments.items():
            if name not in vars.scalar_vars and name not in vars.vector_vars:
                raise ValueError(
                    f"batch_assign parameter '{name}' is not found in analog circuit."
                )
            if name in vars.vector_vars:
                self._assignments[name] = cast_vector_param(value, name)
            else:
                self._assignments[name] = cast_scalar_param(value, name)


class BatchAssign(AssignBase, Flattenable, Parallelizable, BackendRoute, Parse):
    __match_args__ = ("_assignments", "__parent__")

    def __init__(self, parent: Optional[Builder] = None, **assignments) -> None:
        from bloqade.codegen.common.scan_variables import ScanVariablesAnalogCircuit

        super().__init__(parent)

        circuit = self.parse_circuit()
        vars = ScanVariablesAnalogCircuit().emit(circuit)

        self._assignments = {}
        for name, values in assignments.items():
            if name not in vars.scalar_vars and name not in vars.vector_vars:
                raise ValueError(
                    f"batch_assign parameter '{name}' is not found in analog circuit."
                )
            if name in vars.vector_vars:
                self._assignments[name] = cast_batch_vector_param(values, name)
            else:
                self._assignments[name] = cast_batch_scalar_param(values, name)

        if not len(np.unique(list(map(len, assignments.values())))) == 1:
            raise ValueError(
                "all the assignment variables need to have same number of elements."
            )
