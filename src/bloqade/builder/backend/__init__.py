try:
    __import__("pkg_resources").declare_namespace(__name__)
except ImportError:
    __path__ = __import__("pkgutil").extend_path(__path__, __name__)

from bloqade.builder.backend.quera import QuEraService
from bloqade.builder.backend.braket import BraketService
from bloqade.builder.backend.bloqade import BloqadeService


class BackendRoute(QuEraService, BraketService, BloqadeService):
    """
    Specify the backend to run your program on via a string
    (versus more formal builder syntax) of specifying the vendor/product first
    (Bloqade/Braket) and narrowing it down
    (e.g: ...device("quera.aquila") versus ...quera.aquila())
    - You can pass the following arguments:
        - `"braket.aquila"`
        - `"braket.local_emulator"`
        - `"bloqade.python"`
        - `"bloqade.julia"`

    """

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
