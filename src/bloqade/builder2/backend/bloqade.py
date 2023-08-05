from ..base import Builder
from .base import LocalBackend


class Bloqade(Builder):
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
