from bloqade.compiler.codegen.hardware.lattice import AHSLatticeData
from bloqade.compiler.codegen.hardware.piecewise_linear import PiecewiseLinear
from bloqade.compiler.codegen.hardware.piecewise_constant import PiecewiseConstant
from beartype.typing import Optional, List
from pydantic.dataclasses import dataclass
from decimal import Decimal


@dataclass
class AHSComponents:
    lattice_data: AHSLatticeData
    global_detuning: PiecewiseLinear
    global_amplitude: PiecewiseLinear
    global_phase: PiecewiseConstant
    local_detuning: Optional[PiecewiseLinear]
    lattice_site_coefficients: Optional[List[Decimal]]
