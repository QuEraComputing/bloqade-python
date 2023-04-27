from scipy.sparse import csr_matrix
from .sparse_operator import PermMatrix, Diagonal
from numpy.typing import NDArray
from typing import List, Callable, Union
import numpy as np

class Hamiltonian:
    functions: List[Callable]
    operators: List[Union[Diagonal, PermMatrix, csr_matrix]]
    
    def _ode_complex_kernel(self, time: float, register: NDArray):
        result_register = np.zeros_like(register)
        for function, operator in zip(
            self.functions,
            self.operators
        ):
            result_register += \
                function(time) * operator.dot(register)
        
        return result_register
            
    def _ode_real_kernel(self, time: float, register: NDArray):
        # this is needed to use solver that only work on real-valued states
        return self._ode_complex_kernel(
                time, register.view(np.complex128)
            ).view(np.float64)