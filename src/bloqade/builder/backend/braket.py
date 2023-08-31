from bloqade.builder.base import Builder


class BraketService(Builder):
    @property
    def braket(self):
        """
        - Specify braket service
        - Possible Next:

            -> `...braket.aquila`
                :: Aquila QPU, via braket service

            -> `...braket.local_emulator`
                :: braket local emulator backend
        """
        return BraketDeviceRoute(self)


class BraketDeviceRoute(Builder):
    def aquila(self):
        """
        Specify QuEra's Aquila QPU

        Return:
            BraketHardwareRoutine

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

        return Routine(self).braket.aquila()

    def local_emulator(self):
        """
        Using Braket local emulator

        Return:
            BraketLocalEmulatorRoutine


        - Possible Next:

            -> `...local_emulator().run`
                :: run on local emulator

        """
        from bloqade.ir.routine.base import Routine

        return Routine(self).braket.local_emulator()
