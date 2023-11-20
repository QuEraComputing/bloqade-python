from collections import OrderedDict
from pydantic.dataclasses import dataclass
import json

from bloqade.builder.typing import LiteralType
from bloqade.ir.routine.base import RoutineBase, __pydantic_dataclass_config__
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.mock import MockBackend
from bloqade.submission.load_config import load_config
from bloqade.task.batch import RemoteBatch
from bloqade.task.quera import QuEraTask

from beartype.typing import Tuple, Union, Optional
from beartype import beartype


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class QuEraServiceOptions(RoutineBase):
    @beartype
    def device(self, config_file: Optional[str], **api_config):
        if config_file is not None:
            with open(config_file, "r") as f:
                api_config = {**json.load(f), **api_config}

        backend = QuEraBackend(**api_config)

        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)

    def aquila(self) -> "QuEraHardwareRoutine":
        backend = QuEraBackend(**load_config("Aquila"))
        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)

    def cloud_mock(self) -> "QuEraHardwareRoutine":
        backend = QuEraBackend(**load_config("Mock"))
        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)

    @beartype
    def mock(
        self, state_file: str = ".mock_state.txt", submission_error: bool = False
    ) -> "QuEraHardwareRoutine":
        backend = MockBackend(state_file=state_file, submission_error=submission_error)
        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class QuEraHardwareRoutine(RoutineBase):
    backend: Union[QuEraBackend, MockBackend]

    def _compile(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
    ) -> RemoteBatch:
        from bloqade.transform.common.assign_variables import AssignBloqadeIR
        from bloqade.analysis.common.assignment_scan import AssignmentScan
        from bloqade.codegen.hardware.quera import AHSCodegen

        circuit, params = self.circuit, self.params
        capabilities = self.backend.get_capabilities()
        circuit = AssignBloqadeIR(params.static_params).visit(circuit)

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            record_params = AssignmentScan(batch_params).emit(circuit)
            final_circuit = AssignBloqadeIR(record_params).visit(circuit)
            result = AHSCodegen(shots, capabilities=capabilities).emit(final_circuit)
            task_ir = result.quera_task_ir.discretize(capabilities)
            metadata = {**params.static_params, **record_params}
            tasks[task_number] = QuEraTask(
                None, self.backend, task_ir, metadata, result.parallel_decoder
            )

        batch = RemoteBatch(source=self.source, tasks=tasks, name=name)

        return batch

    @beartype
    def run_async(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        """
        Compile to a RemoteBatch, which contain
            QuEra backend specific tasks,
            and run_async through QuEra service.

        Args:
            shots (int): number of shots
            args (Tuple): additional arguments
            name (str): custom name of the batch
            shuffle (bool): shuffle the order of jobs

        Return:
            RemoteBatch

        """
        batch = self._compile(shots, args, name)
        batch._submit(shuffle, **kwargs)
        return batch

    @beartype
    def run(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        batch = self.run_async(shots, args, name, shuffle, **kwargs)
        batch.pull()
        return batch

    @beartype
    def __call__(
        self,
        *args: LiteralType,
        shots: int = 1,
        name: Optional[str] = None,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        return self.run(shots, args, name, shuffle, **kwargs)
