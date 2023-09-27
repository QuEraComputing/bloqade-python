from itertools import repeat
from beartype.typing import Optional, List, Dict, Set
from bloqade.builder.typing import ParamType
from bloqade.builder.base import Builder
from bloqade.builder.pragmas import Parallelizable, AddArgs, BatchAssignable
from bloqade.builder.backend import BackendRoute
from numbers import Real
from decimal import Decimal
import numpy as np


class CastParams:
    def __init__(self, n_sites: int, scalar_vars: Set[str], vector_vars: Set[str]):
        self.n_sites = n_sites
        self.scalar_vars = scalar_vars
        self.vector_vars = vector_vars

    def cast_scalar_param(self, value: ParamType, name: str) -> Decimal:
        if isinstance(value, (Real, Decimal)):
            return Decimal(str(value))

        raise TypeError(
            f"assign parameter '{name}' must be a real number, "
            f"found type: {type(value)}"
        )

    def cast_vector_param(
        self,
        value: List[ParamType],
        name: str,
    ) -> List[Decimal]:
        if isinstance(value, np.ndarray):
            value = value.tolist()

        if isinstance(value, (list, tuple)):
            if len(value) != self.n_sites:
                raise ValueError(
                    f"assign parameter '{name}' must be a list of length "
                    f"{self.n_sites}, found length: {len(value)}"
                )
            return list(map(self.cast_scalar_param, value, repeat(name, len(value))))

        raise TypeError(
            f"assign parameter '{name}' must be a list of real numbers, "
            f"found type: {type(value)}"
        )

    def cast_params(self, params: Dict[str, ParamType]) -> Dict[str, ParamType]:
        checked_params = {}
        for name, value in params.items():
            if name not in self.scalar_vars and name not in self.vector_vars:
                raise ValueError(
                    f"assign parameter '{name}' is not found in analog circuit."
                )
            if name in self.vector_vars:
                checked_params[name] = self.cast_vector_param(value, name)
            else:
                checked_params[name] = self.cast_scalar_param(value, name)

        return checked_params


class AssignBase(Builder):
    pass


class Assign(BatchAssignable, AddArgs, Parallelizable, BackendRoute, AssignBase):
    __match_args__ = ("_assignments", "__parent__")

    def __init__(
        self, assignments: Dict[str, ParamType], parent: Optional[Builder] = None
    ) -> None:
        from bloqade.ir.analysis.scan_variables import ScanVariablesAnalogCircuit

        super().__init__(parent)

        circuit = self.parse_circuit()
        variables = ScanVariablesAnalogCircuit().emit(circuit)

        self._static_params = CastParams(
            circuit.register.n_sites, variables.scalar_vars, variables.vector_vars
        ).cast_params(assignments)


class BatchAssign(AddArgs, Parallelizable, BackendRoute, AssignBase):
    __match_args__ = ("_assignments", "__parent__")

    def __init__(
        self, assignments: Dict[str, ParamType], parent: Optional[Builder] = None
    ) -> None:
        from bloqade.ir.analysis.scan_variables import ScanVariablesAnalogCircuit

        super().__init__(parent)

        circuit = self.parse_circuit()
        variables = ScanVariablesAnalogCircuit().emit(circuit)

        if not len(np.unique(list(map(len, assignments.values())))) == 1:
            raise ValueError(
                "all the assignment variables need to have same number of elements."
            )

        tuple_iterators = [
            zip(repeat(name), values) for name, values in assignments.items()
        ]

        caster = CastParams(
            circuit.register.n_sites, variables.scalar_vars, variables.vector_vars
        )

        self._batch_params = list(
            map(caster.cast_params, map(dict, zip(*tuple_iterators)))
        )


class ListAssign(AddArgs, Parallelizable, BackendRoute, AssignBase):
    def __init__(
        self, batch_params: List[Dict[str, ParamType]], parent: Optional[Builder] = None
    ) -> None:
        from bloqade.ir.analysis.scan_variables import ScanVariablesAnalogCircuit

        super().__init__(parent)

        circuit = self.parse_circuit()
        variables = ScanVariablesAnalogCircuit().emit(circuit)
        caster = CastParams(
            circuit.register.n_sites, variables.scalar_vars, variables.vector_vars
        )

        self._batch_params = list(map(caster.cast_params, batch_params))
