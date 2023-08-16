from typing import Optional
from ..base import Builder
from .base import RemoteBackend
import bloqade.ir as ir
import os
import json
from bloqade.task2.quera import QuEraTask


class QuEraService(Builder):
    @property
    def quera(self):
        return QuEraDeviceRoute(self)


class QuEraDeviceRoute(Builder):
    def aquila(
        self, nshots: int, config_file: Optional[str] = None, **api_configs
    ) -> "Aquila":
        return Aquila(nshots, config_file, self, **api_configs)

    def gemini(
        self, nshots: int, config_file: Optional[str] = None, **api_configs
    ) -> "Gemini":
        return Gemini(nshots, config_file, self, **api_configs)

    def mock(self, nshots: int, state_file: str = ".mock_state.txt") -> "Mock":
        return Mock(nshots, state_file, self)


class QuEraBackend(RemoteBackend):
    __service_name__ = "quera"

    def __init__(
        self,
        config_file: Optional[str] = None,
        parent: Optional[Builder] = None,
        **api_configs,
    ) -> None:
        super().__init__(parent)
        # self._config_file = config_file

        if config_file is None:
            path = os.path.dirname(__file__)

            config_file = os.path.join(
                path,
                "..",
                "submission",
                "quera_api_client",
                "config",
                "integ_quera_api.json",
            )

        if len(api_configs) == 0:
            with open(config_file, "r") as io:
                api_configs.update(**json.load(io))

        self._api_configs = api_configs

    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        backend = QuEraBackend(self._api_configs)
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        capabilities = backend.get_capabilities()
        schema_compiler = SchemaCodeGen([], capabilities=capabilities)
        task_ir = schema_compiler.emit(shots, self.program)
        task_ir = task_ir.discretize(capabilities)
        return QuEraTask(
            task_ir=task_ir,
            backend=backend,
            parallel_decoder=schema_compiler.parallel_decoder,
        )


class Aquila(QuEraBackend):
    __device_name__ = "aquila"


class Gemini(QuEraBackend):
    __device_name__ = "gemini"


class Mock(RemoteBackend):
    __service_name__ = "quera"
    __device_name__ = "mock"

    def __init__(
        self,
        state_file: str = ".mock_state.txt",
        parent: Builder | None = None,
    ) -> None:
        super().__init__(parent)
        self._state_file = state_file
        # [TODO]
