from collections import OrderedDict
from dataclasses import dataclass
import json

from bloqade.builder.typing import LiteralType
from bloqade.ir.routine.base import RoutineBase
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.mock import MockBackend
from bloqade.submission.quera_api_client.load_config import load_config
from bloqade.task.batch import RemoteBatch
from bloqade.task.quera import QuEraTask

from beartype.typing import Tuple, Union, Optional
from beartype import beartype


@dataclass(frozen=True)
class QuEraServiceOptions(RoutineBase):
    @beartype
    def device(self, config_file: Optional[str], **api_config):
        if config_file is not None:
            with open(config_file, "r") as f:
                api_config = {**json.load(f), **api_config}

        backend = QuEraBackend(**api_config)

        return QuEraHardwareRoutine(source=self.source, backend=backend)

    def aquila(self) -> "QuEraHardwareRoutine":
        backend = QuEraBackend(**load_config("Aquila"))
        return QuEraHardwareRoutine(source=self.source, backend=backend)

    def cloud_mock(self) -> "QuEraHardwareRoutine":
        backend = QuEraBackend(**load_config("Mock"))
        return QuEraHardwareRoutine(source=self.source, backend=backend)

    @beartype
    def mock(self, state_file: str = ".mock_state.txt") -> "QuEraHardwareRoutine":
        backend = MockBackend(state_file=state_file)
        return QuEraHardwareRoutine(source=self.source, backend=backend)


@dataclass(frozen=True)
class QuEraHardwareRoutine(RoutineBase):
    backend: Union[QuEraBackend, MockBackend]

    def _compile(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
    ) -> RemoteBatch:
        """
        Compile to a RemoteBatch, which contain
            QuEra backend specific tasks.

        Args:
            shots (int): number of shots
            args (Tuple): additional arguments
            name (str): custom name of the batch

        Return:
            RemoteBatch

        """
        from bloqade.codegen.common.assign_variables import AssignAnalogCircuit

        from bloqade.codegen.common.assignment_scan import AssignmentScan
        from bloqade.codegen.hardware.quera import QuEraCodeGen

        circuit, params = self.parse_source()
        capabilities = self.backend.get_capabilities()
        circuit = AssignAnalogCircuit(params.static_params).visit(circuit)

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            record_params = AssignmentScan(batch_params).emit(circuit)
            final_circuit = AssignAnalogCircuit(record_params).visit(circuit)
            task_ir, parallel_decoder = QuEraCodeGen(capabilities=capabilities).emit(
                shots, final_circuit
            )

            task_ir = task_ir.discretize(capabilities)
            tasks[task_number] = QuEraTask(
                None, self.backend, task_ir, batch_params, parallel_decoder
            )

        batch = RemoteBatch(source=self.source, tasks=tasks, name=name)

        return batch

    @beartype
    def submit(
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
            and submit through QuEra service.

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
        batch = self.submit(shots, args, name, shuffle, **kwargs)
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
