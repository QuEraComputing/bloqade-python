from ..base import Builder
from .base import LocalBackend, FlattenedBackend


class SubmitBloqade(Builder):
    @property
    def bloqade(self):
        return BloqadeDevice(self)


class BloqadeDevice(Builder):
    def python(self, solver: str):
        return BloqadePython(solver, self)

    def julia(self, solver: str, nthreads: int = 1):
        return BloqadeJulia(solver, nthreads, self)


class BloqadePython(LocalBackend):
    def __init__(self, solver: str, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._solver = solver


class BloqadeJulia(LocalBackend):
    def __init__(
        self, solver: str, nthreads: int = 1, parent: Builder | None = None
    ) -> None:
        super().__init__(parent)
        self._solver = solver
        self._nthreads = nthreads


class FlattenedBloqade(Builder):
    @property
    def bloqade(self):
        return FlattenedBloqadeDevice(self)


class FlattenedBloqadeDevice(Builder):
    def python(self, solver: str):
        return FlattenedBloqadePython(solver, self)

    def julia(self, solver: str, nthreads: int = 1):
        return FlattenedBloqadeJulia(solver, nthreads, self)


class FlattenedBloqadePython(FlattenedBackend):
    def __init__(self, solver: str, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._solver = solver


class FlattenedBloqadeJulia(FlattenedBackend):
    def __init__(
        self, solver: str, nthreads: int = 1, parent: Builder | None = None
    ) -> None:
        super().__init__(parent)
        self._solver = solver
        self._nthreads = nthreads
