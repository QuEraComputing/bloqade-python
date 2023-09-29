from itertools import repeat
from beartype.typing import Optional, List, Dict, Set, Sequence, Union
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
        value: Union[np.ndarray, List[ParamType]],
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
        self, assignments: Dict[str, List[ParamType]], parent: Optional[Builder] = None
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
        self,
        batch_params: Sequence[Dict[str, ParamType]],
        parent: Optional[Builder] = None,
    ) -> None:
        from bloqade.ir.analysis.scan_variables import ScanVariablesAnalogCircuit

        super().__init__(parent)

        circuit = self.parse_circuit()
        variables = ScanVariablesAnalogCircuit().emit(circuit)
        caster = CastParams(
            circuit.register.n_sites, variables.scalar_vars, variables.vector_vars
        )

        keys = set([])
        for params in batch_params:
            keys.update(params.keys())

        for batch_num, params in enumerate(batch_params):
            curr_keys = set(params.keys())
            missing_keys = keys.difference(curr_keys)
            if missing_keys:
                raise ValueError(
                    f"Batch {batch_num} missing key(s): {tuple(missing_keys)}."
                )

        self._batch_params = list(map(caster.cast_params, batch_params))
