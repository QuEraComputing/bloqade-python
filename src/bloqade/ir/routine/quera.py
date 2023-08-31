from collections import OrderedDict
from dataclasses import dataclass
import json
from numbers import Real

from bloqade.ir.routine.base import RoutineBase
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.mock import MockBackend
from bloqade.submission.quera_api_client.load_config import load_config
from bloqade.task.batch import RemoteBatch
from bloqade.task.quera import QuEraTask

from typing import Tuple, Union


@dataclass(frozen=True)
class QuEraServiceOptions(RoutineBase):
    def device(self, config_file: str | None, **api_config):
        if config_file is not None:
            with open(config_file, "r") as f:
                api_config = {**json.load(f), **api_config}

        backend = QuEraBackend(**api_config)

        return QuEraHardwareRoutine(source=self.source, backend=backend)

    def aquila(self) -> "QuEraHardwareRoutine":
        backend = QuEraBackend(**load_config("Aquila"))
        return QuEraHardwareRoutine(source=self.source, backend=backend)

    def cloud_mock(self):
        backend = QuEraBackend(**load_config("Mock"))
        return QuEraHardwareRoutine(source=self.source, backend=backend)

    def mock(self, state_file: str = ".mock_state.txt"):
        backend = MockBackend(state_file=state_file)
        return QuEraHardwareRoutine(source=self.source, backend=backend)


@dataclass(frozen=True)
class QuEraHardwareRoutine(RoutineBase):
    backend: Union[QuEraBackend, MockBackend]

    def compile(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
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
            final_circuit = AssignAnalogCircuit(batch_params).visit(circuit)
            record_params = AssignmentScan().emit(final_circuit)
            task_ir, parallel_decoder = QuEraCodeGen(
                record_params, capabilities=capabilities
            ).emit(shots, final_circuit)

            task_ir = task_ir.discretize(capabilities)
            tasks[task_number] = QuEraTask(
                None, self.backend, task_ir, batch_params, parallel_decoder
            )

        batch = RemoteBatch(source=self.source, tasks=tasks, name=name)

        return batch

    def submit(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
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
        batch = self.compile(shots, args, name)
        batch._submit(shuffle, **kwargs)
        return batch
