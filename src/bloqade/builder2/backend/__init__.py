from .quera import SubmitQuEra, FlattenedQuEra
from .braket import SubmitBraket, FlattenedBraket
from .bloqade import SubmitBloqade, FlattenedBloqade


class SubmitBackendRoute(SubmitQuEra, SubmitBraket, SubmitBloqade):
    def device(self, name: str, *args, **kwargs):
        if name == "quera.aquila":
            dev = self.quera.aquila
        elif name == "quera.gemini":
            dev = self.quera.gemini
        elif name == "braket.aquila":
            dev = self.braket.aquila
        elif name == "braket.simu":
            dev = self.braket.simu
        elif name == "bloqade.python":
            dev = self.bloqade.python
        elif name == "bloqade.julia":
            dev = self.bloqade.julia
        else:
            raise ValueError(f"Unknown device: {name}")
        return dev(*args, **kwargs)


class FlattenedBackendRoute(FlattenedQuEra, FlattenedBraket, FlattenedBloqade):
    def device(self, name: str, *args, **kwargs):
        if name == "quera.aquila":
            dev = self.quera.aquila
        elif name == "quera.gemini":
            dev = self.quera.gemini
        elif name == "braket.aquila":
            dev = self.braket.aquila
        elif name == "braket.simu":
            dev = self.braket.simu
        elif name == "bloqade.python":
            dev = self.bloqade.python
        elif name == "bloqade.julia":
            dev = self.bloqade.julia
        else:
            raise ValueError(f"Unknown device: {name}")
        return dev(*args, **kwargs)
