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
    def python(self, solver: str):
        raise NotImplementedError

    def julia(self, solver: str, nthreads: int = 1):
        raise NotImplementedError
