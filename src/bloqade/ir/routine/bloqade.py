from .base import RoutineBase
from bloqade.task.batch import LocalBatch
from typing import Tuple
from numbers import Real
from dataclasses import dataclass


@dataclass(frozen=True)
class BloqadeServiceOptions(RoutineBase):
    def python(
        self,
        bloqade_radius: float = 0,
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
        solver: str = "dop853",
    ):
        return BloqadePythonRoutine(source=self.source, bloqade_radius=bloqade_radius)


@dataclass(frozen=True)
class BloqadePythonRoutine(RoutineBase):
    bloqade_radius: float
    atol: float = 1e-7
    rtol: float = 1e-14
    nsteps: int = 2_147_483_647

    def compile(
        self, shots: int, args: Tuple[Real, ...] = (), name: str | None = None
    ) -> LocalBatch:
        from bloqade.codegen.common.assignment_scan import AssignmentScan
        from bloqade.codegen.common.assign_variables import AssignAnalogCircuit
        from bloqade.emulate.codegen.emulator_ir import EmulatorProgramCodeGen
        from bloqade.emulate.codegen.rydberg_hamiltonian import (
            RydbergHamiltonianCodeGen,
        )
        from bloqade.emulate.ir.state_vector import AnalogGate

        circuit, params = self.source.parse_source()

        circuit = AssignAnalogCircuit(params.static_params).visit(circuit)

        gates = {}
        for task_number, batch_param in params.batch_assignments(*args):
            record_params = AssignmentScan(batch_param).emit(circuit)
            final_circuit = AssignAnalogCircuit(record_params).visit(circuit)
            emulator_ir = EmulatorProgramCodeGen().emit(final_circuit)
            hamiltonian = RydbergHamiltonianCodeGen().emit(emulator_ir)

            gate = AnalogGate(hamiltonian)
            gates[task_number] = gate
