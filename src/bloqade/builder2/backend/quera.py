from typing import Optional
from bloqade.builder2.base import Builder
from .base import LocalBackend, RemoteBackend


class QuEra(Builder):
    @property
    def quera(self):
        return QuEraDevice(self)


class QuEraDevice(Builder):
    def aquila(
        self, nshots: int, config_file: Optional[str] = None, **api_configs
    ) -> "Aquila":
        return Aquila(nshots, config_file, self, **api_configs)

    def simu(self, solver: str) -> "Simu":
        return Simu(solver, self)

    def mock(self, nshots: int, state_file: str = ".mock_state.txt") -> "Mock":
        return Mock(nshots, state_file, self)


class Aquila(RemoteBackend):
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


class Simu(LocalBackend):
    def __init__(self, solver: str, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._solver = solver


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
