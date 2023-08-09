from ..base import Builder
from .base import LocalBackend, FlattenedBackend


class SubmitBloqade(Builder):
    @property
    def bloqade(self):
        return BloqadeDeviceRoute(self)


class BloqadeDeviceRoute(Builder):
    def python(self, solver: str):
        return BloqadePython(solver, self)

    def julia(self, solver: str, nthreads: int = 1):
        return BloqadeJulia(solver, nthreads, self)


class SubmitBloqadeBackend(LocalBackend):
    __service_name__ = "bloqade"

    def __init__(self, solver: str, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._solver = solver


class BloqadePython(SubmitBloqadeBackend):
    __device_name__ = "python"


class BloqadeJulia(SubmitBloqadeBackend):
    __device_name__ = "julia"

    def __init__(
        self, solver: str, nthreads: int = 1, parent: Builder | None = None
    ) -> None:
        super().__init__(solver, parent)
        self._nthreads = nthreads


class FlattenedBloqade(Builder):
    @property
    def bloqade(self):
        return FlattenedBloqadeDeviceRoute(self)


class FlattenedBloqadeDeviceRoute(Builder):
    def python(self, solver: str):
        return FlattenedBloqadePython(solver, self)

    def julia(self, solver: str, nthreads: int = 1):
        return FlattenedBloqadeJulia(solver, nthreads, self)


class FlattenedBloqadeBackend(FlattenedBackend):
    __service_name__ = "bloqade"


class FlattenedBloqadePython(FlattenedBloqadeBackend):
    ___device_name__ = "python"

    def __init__(self, solver: str, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._solver = solver


class FlattenedBloqadeJulia(FlattenedBloqadeBackend):
    ___device_name__ = "julia"

    def __init__(
        self, solver: str, nthreads: int = 1, parent: Builder | None = None
    ) -> None:
        super().__init__(parent)
        self._solver = solver
        self._nthreads = nthreads
