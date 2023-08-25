from typing import Optional
from bloqade.builder.base import Builder
from bloqade.builder.backend.base import RemoteBackend
from bloqade.task.quera import QuEraTask
import bloqade.submission.quera as quera_submit
import bloqade.submission.mock as mock_submit
import os
import json

class QuEraService(Builder):
    @property
    def quera(self):
        return QuEraDeviceRoute(self)


class QuEraDeviceRoute(Builder):
    def aquila(self, config_file: Optional[str] = None, **api_configs) -> "Aquila":
        return Aquila(config_file, parent=self, **api_configs)

    def gemini(self, config_file: Optional[str] = None, **api_configs) -> "Gemini":
        return Gemini(config_file, parent=self, **api_configs)

    def mock(
        self,
        state_file: str = ".mock_state.txt",
    ) -> "Mock":
        return Mock(state_file, parent=self)


class QuEraBackend(RemoteBackend):
    __service_name__ = "quera"

    def __init__(
        self,
        config_file: Optional[str] = None,
        parent: Optional[Builder] = None,
        # cache_compiled_programs: bool = False,
        **api_configs,
    ) -> None:
        # super().__init__(cache_compiled_programs, parent=parent)
        super().__init__(parent=parent)
        # self._config_file = config_file

        if config_file is None:
            path = os.path.dirname(__file__)

            config_file = os.path.join(
                path,
                "../..",
                "submission",
                "quera_api_client",
                "config",
                "integ_quera_api.json",
            )

        if len(api_configs) == 0:
            with open(config_file, "r") as io:
                api_configs.update(**json.load(io))

        self._api_configs = api_configs

    def compile_taskdata(self, shots, *args):
        backend = quera_submit.QuEraBackend(self._api_configs)
        return self._compile_taskdata(shots, backend, *args)

    def _compile_taskdata(self, shots, backend, *args):
        from bloqade.builder.compile.quera import QuEraSchemaCompiler

        capabilities = backend.get_capabilities()

        quera_task_data_list = QuEraSchemaCompiler(self, capabilities).compile(
            shots, *args
        )
        return quera_task_data_list

    def compile_tasks(self, shots, *args):
        backend = quera_submit.QuEraBackend(**self._api_configs)
        task_data = self._compile_taskdata(shots, backend, *args)

        return [QuEraTask(task_data=dat, backend=backend) for dat in task_data]

    """"
    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        backend = quera_submit.QuEraBackend(self._api_configs)
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        capabilities = backend.get_capabilities()
        schema_compiler = SchemaCodeGen([], capabilities=capabilities)
        task_ir = schema_compiler.emit(shots, bloqade_ir)
        task_ir = task_ir.discretize(capabilities)
        return QuEraTask(
            task_ir=task_ir,
            backend=backend,
            parallel_decoder=schema_compiler.parallel_decoder,
        )
    """


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
        # cache_compiled_programs: bool = False,
        parent: Builder | None = None,
    ) -> None:
        # super().__init__(cache_compiled_programs, parent=parent)
        super().__init__(parent=parent)
        self._state_file = state_file

    """
    def compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        backend = mock_submit.DumbMockBackend(state_file=self._state_file)
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        capabilities = backend.get_capabilities()
        schema_compiler = SchemaCodeGen([], capabilities=capabilities)
        task_ir = schema_compiler.emit(shots, bloqade_ir)
        task_ir = task_ir.discretize(capabilities)
        return QuEraTask(
            task_ir=task_ir,
            backend=backend,
            parallel_decoder=schema_compiler.parallel_decoder,
        )
    """

    def compile_taskdata(self, shots, *args):
        backend = mock_submit.DumbMockBackend(state_file=self._state_file)
        return self._compile_taskdata(shots, backend, *args)

    def _compile_taskdata(self, shots, backend, *args):
        from bloqade.builder.compile.quera import QuEraSchemaCompiler

        capabilities = backend.get_capabilities()

        quera_task_data_list = QuEraSchemaCompiler(self, capabilities).compile(
            shots, *args
        )
        return quera_task_data_list

    def compile_tasks(self, shots, *args):
        backend = mock_submit.DumbMockBackend(state_file=self._state_file)
        task_data = self._compile_taskdata(shots, backend, *args)

        return [QuEraTask(task_data=dat, backend=backend) for dat in task_data]
