from .base import Lattice
from typing import List, Tuple


class Square(Lattice):
    def __init__(self, L: int) -> None:
        super().__init__()
        self.L = L
        self._positions = None

    def positions(self) -> List[Tuple[float, float]]:
        if self._positions:
            return self._positions

        self._positions = [(x, y) for x in range(self.L) for y in range(self.L)]
        return self._positions
