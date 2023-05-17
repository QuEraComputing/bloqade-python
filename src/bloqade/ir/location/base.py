from bloqade.builder.start import ProgramStart
from numpy.typing import NDArray
from typing import Generator
from bokeh.plotting import show


class AtomArrangement(ProgramStart):
    def __init__(self) -> None:
        super().__init__(register=self)

    def enumerate(self) -> Generator[NDArray, None, None]:
        """enumerate all positions in the register."""
        raise NotImplementedError

    def figure(self):
        """plot the register."""
        raise NotImplementedError

    def show(self) -> None:
        """show the register."""
        show(self.figure())

    @property
    def n_atoms(self):
        raise NotImplementedError

    @property
    def n_dims(self):
        raise NotImplementedError
