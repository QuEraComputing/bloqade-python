from typing import Optional
from bloqade.builder.base import Builder


class QuEraService(Builder):
    @property
    def quera(self):
        return QuEraDeviceRoute(self)


class QuEraDeviceRoute(Builder):
    def aquila(self, config_file: Optional[str] = None, **api_configs):
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.aquila(config_file, **api_configs)

    def mock(self, state_file: str = ".mock_state.txt"):
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.mock(state_file)
