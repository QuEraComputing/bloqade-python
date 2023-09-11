from typing import Optional
from bloqade.builder.base import Builder


class QuEraService(Builder):
    @property
    def quera(self):
        """
        - Specify Quera backend
        - Possible Next:

            -> `...quera.aquila`
                :: Aquila QPU

            -> `...quera.mock`
                :: mock backend, meant for testings

            -> `...quera.device`
                :: QuEra QPU, specifiy by config_file

        """
        return QuEraDeviceRoute(self)


class QuEraDeviceRoute(Builder):
    def device(self, config_file: Optional[str] = None, **api_config):
        """
        Specify QuEra's QPU device,

        Args:
            config_file (str): file that speficy the target hardware

        Return:
            QuEraHardwareRoutine

        - Possible Next:

            -> `...device().submit`
                :: submit aync remote job

            -> `...device().run`
                :: submit job and wait until job finished
                and results returned

            -> `...device().__callable__`
                :: submit job and wait until job finished
                and results returned


        """
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.device(config_file, **api_config)

    def aquila(self):
        """
        Specify QuEra's Aquila QPU

        Return:
            QuEraHardwareRoutine


        - Possible Next:

            -> `...aquila().submit`
                :: submit aync remote job

            -> `...aquila().run`
                :: submit job and wait until job finished
                and results returned

            -> `...aquila().__callable__`
                :: submit job and wait until job finished
                and results returned


        """
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.aquila()

    def cloud_mock(self):
        """
        Specify QuEra's Remote Mock QPU

        Return:
            QuEraHardwareRoutine

        - Possible Next:

            -> `...aquila().submit`
                :: submit aync remote job

            -> `...aquila().run`
                :: submit job and wait until job finished
                and results returned

            -> `...aquila().__callable__`
                :: submit job and wait until job finished
                and results returned



        """
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.cloud_mock()

    def mock(self, state_file: str = ".mock_state.txt"):
        """
        Specify mock, testing locally.

        Return:
            QuEraHardwareRoutine

        - Possible Next:

            -> `...aquila().submit`
                :: submit aync remote job

            -> `...aquila().run`
                :: submit job and wait until job finished
                and results returned

            -> `...aquila().__callable__`
                :: submit job and wait until job finished
                and results returned



        """
        from bloqade.ir.routine.base import Routine

        return Routine(self).quera.mock(state_file)
