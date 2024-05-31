"""
This module defines the BloqadeTask class, which is used to execute quantum tasks using the 
Bloqade emulator. It also provides serialization and deserialization methods for the BloqadeTask 
instances.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
from beartype.typing import Dict, Any

from bloqade.serialize import Serializer
from bloqade.task.base import Geometry, LocalTask
from bloqade.emulate.ir.emulator import EmulatorProgram
from bloqade.emulate.codegen.hamiltonian import (
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
from bloqade.builder.base import ParamType


@dataclass
@Serializer.register
class BloqadeTask(LocalTask):
    """
    Represents a quantum task to be executed on the Bloqade emulator.

    Attributes:
        shots (int): The number of shots to be executed.
        emulator_ir (EmulatorProgram): The emulation program to be executed.
        metadata (Dict[str, ParamType]): Metadata associated with the task.
        compile_cache (Optional[CompileCache]): Cache for compiled code.
        task_result_ir (Optional[QuEraTaskResults]): Results of the task execution.
    """

    shots: int
    emulator_ir: EmulatorProgram
    metadata: Dict[str, ParamType]
    compile_cache: Optional[CompileCache] = None
    task_result_ir: Optional[QuEraTaskResults] = None

    def _geometry(self) -> Geometry:
        """
        Returns the geometry of the qubit register.

        Returns:
            Geometry: The geometry of the qubit register.
        """
        return self.emulator_ir.register.geometry

    def result(self) -> QuEraTaskResults:
        """
        Returns the results of the task execution.

        Returns:
            QuEraTaskResults: The results of the task execution.
        """
        return self.task_result_ir

    @property
    def nshots(self) -> int:
        """
        Returns the number of shots to be executed.

        Returns:
            int: The number of shots to be executed.
        """
        return self.shots

    def run(
        self,
        solver_name: str = "dop853",
        atol: float = 1e-14,
        rtol: float = 1e-7,
        nsteps: int = 2_147_483_647,
        interaction_picture: bool = False,
    ) -> "BloqadeTask":
        """
        Runs the quantum task using the specified solver and options.

        Args:
            solver_name (str): The name of the solver to be used. Default is "dop853".
            atol (float): Absolute tolerance for the solver. Default is 1e-14.
            rtol (float): Relative tolerance for the solver. Default is 1e-7.
            nsteps (int): Maximum number of steps for the solver. Default is 2_147_483_647.
            interaction_picture (bool): Whether to use the interaction picture. Default is False.

        Returns:
            BloqadeTask: The current instance with updated task results.

        Raises:
            ValueError: If there is an error during the execution of the task.
        """
        hamiltonian = RydbergHamiltonianCodeGen(self.compile_cache).emit(
            self.emulator_ir
        )
        options = dict(
            solver_name=solver_name,
            atol=atol,
            rtol=rtol,
            nsteps=nsteps,
            interaction_picture=interaction_picture,
        )
        shots_array = AnalogGate(hamiltonian).run(
            self.shots, project_hyperfine=True, **options
        )

        geometry = self.emulator_ir.register.geometry

        filling = np.asarray(geometry.filling, dtype=int)
        full_shot = np.zeros_like(filling, dtype=int)

        shot_outputs = []
        for shot in shots_array[:]:
            # flip the bits so that 1 = ground state and 0 = excited state
            # and scatter shot results into the full shot array according to the filling
            full_shot[filling == 1] = 1 - shot

            shot_result = QuEraShotResult(
                shot_status=QuEraShotStatusCode.Completed,
                pre_sequence=filling.tolist(),
                post_sequence=full_shot.tolist(),
            )
            shot_outputs.append(shot_result)

        self.task_result_ir = QuEraTaskResults(
            task_status=QuEraTaskStatusCode.Completed, shot_outputs=shot_outputs
        )

        return self


@BloqadeTask.set_serializer
def _serialize(obj: BloqadeTask) -> Dict[str, Any]:
    """
    Serializes a BloqadeTask object to a dictionary.

    Args:
        obj (BloqadeTask): The BloqadeTask object to be serialized.

    Returns:
        Dict[str, Any]: The serialized representation of the BloqadeTask object.
    """
    return {
        "shots": obj.shots,
        "emulator_ir": obj.emulator_ir,
        "metadata": obj.metadata,
        "task_result_ir": obj.task_result_ir.dict() if obj.task_result_ir else None,
    }


@BloqadeTask.set_deserializer
def _deserialize(d: Dict[str, Any]) -> BloqadeTask:
    """
    Deserializes a dictionary to a BloqadeTask object.

    Args:
        d (Dict[str, Any]): The dictionary to be deserialized.

    Returns:
        BloqadeTask: The deserialized BloqadeTask object.
    """
    d["task_result_ir"] = (
        QuEraTaskResults(**d["task_result_ir"]) if d["task_result_ir"] else None
    )
    return BloqadeTask(**d)
