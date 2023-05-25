from .spatial import SpatialModulation
from .coupling import LevelCoupling
from .field import Rabi
from .start import ProgramStart
from .emit import Emit
from bloqade.ir.location.base import ParallelRegister
from typing import Any


class Terminate(SpatialModulation, LevelCoupling, Rabi, ProgramStart, Emit):
    def parallelize(self, cluster_spacing: Any) -> Emit:
        parallel_register = ParallelRegister(self.register, cluster_spacing)
        return Emit(
            self,
            assignments=self.__assignments__,
            batch=self.__batch__,
            register=parallel_register,
            sequence=self.__sequence__,
        )
