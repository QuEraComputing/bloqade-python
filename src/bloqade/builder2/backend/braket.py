from bloqade.builder2.base import Builder
from .base import LocalBackend, RemoteBackend, FlattenedBackend


class SubmitBraket(Builder):
    @property
    def braket(self):
        return BraketDevice(self)


class BraketDevice(Builder):
    def aquila(self, nshots: int) -> "Aquila":
        return Aquila(nshots, self)

    def simu(self, nshots: int) -> "Simu":
        return Simu(nshots, self)


class Aquila(RemoteBackend):
    __service_name__ = "braket"
    __device_name__ = "aquila"

    def __init__(self, nshots: int, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._nshots = nshots


class Simu(LocalBackend):
    __service_name__ = "braket"
    __device_name__ = "simu"

    def __init__(self, nshots: int, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._nshots = nshots


class FlattenedBraket(Builder):
    @property
    def braket(self):
        return FlattenedBraketDevice(self)


class FlattenedBraketDevice(Builder):
    def aquila(self, nshots: int) -> "Aquila":
        return FlattenedAquila(nshots, self)

    def simu(self, nshots: int) -> "Simu":
        return FlattenedSimu(nshots, self)


class FlattenedAquila(FlattenedBackend):
    def __init__(self, parent: Builder | None = None) -> None:
        super().__init__(parent)


class FlattenedSimu(FlattenedBackend):
    def __init__(self, parent: Builder | None = None) -> None:
        super().__init__(parent)
