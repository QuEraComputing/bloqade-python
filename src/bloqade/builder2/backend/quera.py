from typing import Optional
from ..base import Builder
from .base import RemoteBackend


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
        self._config_file = config_file
        self._api_configs = api_configs


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
