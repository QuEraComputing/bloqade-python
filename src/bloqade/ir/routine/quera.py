from collections import OrderedDict
from dataclasses import dataclass
import json
from numbers import Real
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.mock import MockBackend
from bloqade.submission.quera_api_client.load_config import load_config
from bloqade.task.batch import RemoteBatch

from typing import TYPE_CHECKING, Tuple, Union

if TYPE_CHECKING:
    from bloqade.builder.base import Builder


@dataclass(frozen=True)
class QuEraServiceOptions:
    source: "Builder"

    def device(self, config_file: str | None, **api_config):
        if config_file is not None:
            api_config = {**json.load(config_file), **api_config}

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
class QuEraHardwareRoutine:
    source: "Builder"
    backend: Union[QuEraBackend, MockBackend]

    def submit(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        from bloqade.builder.parse.builder import Parser
        from bloqade.codegen.common.static_assign import StaticAssignProgram
        from bloqade.codegen.hardware.quera import QuEraCodeGen
        from bloqade.task.quera import QuEraTask

        circuit, params = Parser().parse(self.source)
        capabilities = self.backend.get_capabilities()
        circuit = StaticAssignProgram(params.static_params).visit(circuit)

        tasks = OrderedDict()

        for task_number, params in enumerate(params.batch_assignments(*args)):
            task_ir, parallel_decoder = QuEraCodeGen(params, capabilities).emit(
                shots, circuit
            )
            tasks[task_number] = QuEraTask(
                None, self.backend, task_ir, params, parallel_decoder
            )

        return RemoteBatch(tasks, shuffle=shuffle, name=name)
