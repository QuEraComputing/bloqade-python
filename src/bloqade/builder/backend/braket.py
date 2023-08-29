from bloqade.builder.base import Builder


class BraketService(Builder):
    @property
    def braket(self):
        return BraketDeviceRoute(self)


class BraketDeviceRoute(Builder):
    def aquila(self):
        from bloqade.ir.routine.base import Routine

        return Routine(self).braket.aquila()

    def local_emulator(self):
        from bloqade.ir.routine.base import Routine

        return Routine(self).braket.local_emulator()
