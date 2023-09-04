from bloqade.task.base import Geometry, LocalTask
from bloqade.emulate.ir.emulator import EmulatorProgram
from bloqade.emulate.codegen.rydberg_hamiltonian import (
    RydbergHamiltonianCodeGen,
    CompileCache,
)
from bloqade.emulate.ir.state_vector import AnalogGate

from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraShotResult,
    QuEraTaskStatusCode,
    QuEraShotStatusCode,
)

from dataclasses import dataclass
from typing import Optional


@dataclass
class BloqadeTask(LocalTask):
    shots: int
    emulator_ir: EmulatorProgram
    compile_cache: Optional[CompileCache] = None
    task_result_ir: Optional[QuEraTaskResults] = None

    def _geometry(self) -> Geometry:
        sites = [tuple(map(float, site)) for site in self.emulator_ir.geometry.sites]

        return Geometry(sites=sites, filling=[1 for _ in sites], parallel_decoder=None)

    def result(self) -> QuEraTaskResults:
        return self.task_result_ir

    def run(
        self,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
    ) -> "BloqadeTask":
        hamiltonian = RydbergHamiltonianCodeGen(self.compile_cache).emit(
            self.emulator_ir
        )
        shots_array = AnalogGate(hamiltonian).run(
            self.shots, solver_name, atol, rtol, nsteps, project_hyperfine=True
        )

        shot_outputs = []
        for shot in shots_array[:]:
            shot_result = QuEraShotResult(
                shot_status=QuEraShotStatusCode.Completed,
                pre_sequence=[1 for _ in shot],
                post_sequence=list(shot),
            )
            shot_outputs.append(shot_result)

        self.task_result_ir = QuEraTaskResults(
            task_status=QuEraTaskStatusCode.Completed, shot_outputs=shot_outputs
        )

        return self
