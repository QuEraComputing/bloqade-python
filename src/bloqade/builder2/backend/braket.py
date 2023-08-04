from bloqade.builder2.base import Builder
from .base import LocalBackend, RemoteBackend


class Braket(Builder):
    @property
    def braket(self):
        return BraketDevice(self)


class BraketDevice(Builder):
    def aquila(self, nshots: int) -> "Aquila":
        return Aquila(nshots, self)

    def simu(self, nshots: int) -> "Simu":
        return Simu(nshots, self)


class Aquila(RemoteBackend):
    def __init__(self, nshots: int, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._nshots = nshots


class Simu(LocalBackend):
    def __init__(self, nshots: int, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._nshots = nshots
