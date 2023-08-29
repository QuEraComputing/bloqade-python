from bloqade.builder.base import Builder


class QuEraService(Builder):
    @property
    def quera(self):
        return QuEraDeviceRoute(self)


class QuEraDeviceRoute(Builder):
    def device(self, config_file: str | None = None, **api_config):
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.device(config_file, **api_config)

    def aquila(self):
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.aquila()

    def cloud_mock(self):
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.cloud_mock()

    def mock(self, state_file: str = ".mock_state.txt"):
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.mock(state_file)
