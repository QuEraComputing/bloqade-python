from .base import RoutineBase
from bloqade.task.batch import LocalBatch
from typing import Tuple, Union
from numbers import Real


class BloqadeServiceOptions(RoutineBase):
    def python(self):
        return BloqadePythonRoutine(source=self.source)


class BloqadePythonRoutine(RoutineBase):
    def compile(
        self, shots: int, args: Tuple[Real, ...] = (), name: str | None = None
    ) -> LocalBatch:
        from bloqade.codegen.common.assign_variables import AssignAnalogCircuit
        from bloqade.emulate.codegen.emulator_ir import EmulatorProgramCodeGen
        from bloqade.emulate.codegen.rydberg_hamiltonian import (
            RydbergHamiltonianCodeGen,
        )

        circuit, params = self.source.parse_source()

        circuit = AssignAnalogCircuit(params.static_params).visit(circuit)

        for task_number, batch_param in params.batch_assignments(*args):
            final_circuit = AssignAnalogCircuit(batch_param).visit(circuit)
