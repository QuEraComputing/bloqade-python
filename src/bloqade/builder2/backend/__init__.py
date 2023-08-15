from .quera import QuEraService
from .braket import BraketService
from .bloqade import BloqadeService


class BackendRoute(QuEraService, BraketService, BloqadeService):
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
