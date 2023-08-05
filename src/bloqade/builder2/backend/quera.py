from typing import Optional
from ..base import Builder
from .base import RemoteBackend


class QuEra(Builder):
    @property
    def quera(self):
        return QuEraDevice(self)


class QuEraDevice(Builder):
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
    def __init__(
        self,
        nshots: int,
        config_file: Optional[str] = None,
        parent: Optional[Builder] = None,
        **api_configs,
    ) -> None:
        super().__init__(parent)
        self._nshots = nshots
        self._config_file = config_file
        self._api_configs = api_configs


class Aquila(QuEraBackend):
    pass


class Gemini(QuEraBackend):
    pass


class Mock(RemoteBackend):
    def __init__(
        self,
        nshots: int,
        state_file: str = ".mock_state.txt",
        parent: Builder | None = None,
    ) -> None:
        super().__init__(parent)
        self._nshots = nshots
        self._state_file = state_file
