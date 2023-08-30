from bloqade.builder.backend.quera import QuEraService
from bloqade.builder.backend.braket import BraketService
from bloqade.builder.backend.bloqade import BloqadeService


class BackendRoute(QuEraService, BraketService, BloqadeService):
    def device(self, name: str, *args, **kwargs):
        if name == "quera.aquila":
            dev = self.quera.aquila
        elif name == "braket.aquila":
            dev = self.braket.aquila
        elif name == "braket.local_emulator":
            dev = self.braket.local_emulator
        elif name == "bloqade.python":
            dev = self.bloqade.python
        elif name == "bloqade.julia":
            dev = self.bloqade.julia
        else:
            raise ValueError(f"Unknown device: {name}")
        return dev(*args, **kwargs)
