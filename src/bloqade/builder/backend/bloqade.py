from bloqade.builder.base import Builder


class BloqadeService(Builder):
    @property
    def bloqade(self):
        """
        - Specify bloqade emulator
        - Possible Next:

            -> `...bloqade.python`
                :: Bloqade python backend

            -> `...bloqade.julia`
                :: Bloqade julia backend
        """
        return BloqadeDeviceRoute(self)


class BloqadeDeviceRoute(Builder):
    def python(self):
        """
        - Specify bloqade python backend
        - Possible Next:

            -> `...python().run(shots, ...)`
                :: Run the current program using bloqade python backend
        """
        from bloqade.ir.routine.bloqade import BloqadeServiceOptions

        return BloqadeServiceOptions(self).python()

    def julia(self, solver: str, nthreads: int = 1):
        raise NotImplementedError
