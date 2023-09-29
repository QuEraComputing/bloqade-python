from bloqade.builder.base import Builder


class BloqadeService(Builder):
    @property
    def bloqade(self):
        """
        Specify the Bloqade backend.

        - Possible Next Steps:
            - |_ `...bloqade.python()`: target submission to the Bloqade python backend
            - |_ `...bloqade.julia()`: (CURRENTLY NOT IMPLEMENTED!)target 
                submission to the Bloqade.jl backend
        """
        return BloqadeDeviceRoute(self)


class BloqadeDeviceRoute(Builder):
    def python(self):
        """
        Specify the Bloqade Python backend.

        - Possible Next Steps:
            - |_ `...python().run(shots)`: 
                to submit to the python emulator and await results
        """
        return self.parse().bloqade.python()

    def julia(self, solver: str, nthreads: int = 1):
        raise NotImplementedError
