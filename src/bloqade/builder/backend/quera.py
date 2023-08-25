from typing import Optional
from bloqade.builder.base import Builder
from bloqade.builder.backend.base import RemoteBackend
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

    def compile(self, shots, args, name: Optional[str] = None):
        from bloqade.builder.parse.builder import Parser
        from bloqade.submission.quera import QuEraBackend
        from bloqade.compile.quera import QuEraBatchCompiler

        backend = QuEraBackend(**self._api_configs)
        program = Parser(self).parse()
        return QuEraBatchCompiler(program, backend).compile(shots, args, name)


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
        super().__init__(parent=parent)
        self._state_file = state_file

    def compile(self, shots, args, name: Optional[str] = None):
        from bloqade.builder.parse.builder import Parser
        from bloqade.compile.quera import QuEraBatchCompiler
        from bloqade.submission.mock import DumbMockBackend

        backend = DumbMockBackend(self._state_file)
        program = Parser(self).parse()
        return QuEraBatchCompiler(program, backend).compile(shots, args, name)
