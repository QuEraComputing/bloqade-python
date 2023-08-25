from bloqade.builder.base import Builder
from bloqade.builder.base import LocalBackend


class BloqadeService(Builder):
    @property
    def bloqade(self):
        return BloqadeDeviceRoute(self)


class BloqadeDeviceRoute(Builder):
    def python(self, solver: str):
        return BloqadePython(solver, parent=self)

    def julia(self, solver: str, nthreads: int = 1):
        return BloqadeJulia(solver, nthreads, parent=self)


class SubmitBloqadeBackend(LocalBackend):
    __service_name__ = "bloqade"

    def __init__(
        self,
        solver: str,
        cache_compiled_program: bool = False,
        parent: Builder | None = None,
    ) -> None:
        # super().__init__(cache_compiled_program, parent=parent)
        super().__init__(parent=parent)
        self._solver = solver


class BloqadePython(SubmitBloqadeBackend):
    __device_name__ = "python"


class BloqadeJulia(SubmitBloqadeBackend):
    __device_name__ = "julia"

    def __init__(
        self,
        solver: str,
        nthreads: int = 1,
        cache_compiled_program: bool = False,
        parent: Builder | None = None,
    ) -> None:
        # super().__init__(solver, cache_compiled_program, parent)
        super().__init__(solver, parent)
        self._nthreads = nthreads
