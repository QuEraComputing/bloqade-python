from bloqade.builder.base import Builder


class BloqadeService(Builder):
    @property
    def bloqade(self):
        return BloqadeDeviceRoute(self)


class BloqadeDeviceRoute(Builder):
    def python(self, solver: str):
        from bloqade.ir.routine.base import Routine

        return Routine(self).bloqade.python(solver)

    def julia(self, solver: str, nthreads: int = 1):
        from bloqade.ir.routine.base import Routine

        return Routine(self).bloqade.julia(solver, nthreads)
