from bloqade.codegen.hardware_v2.lattice import AHSLatticeData
from bloqade.codegen.hardware_v2.piecewise_linear import PiecewiseLinear
from bloqade.codegen.hardware_v2.piecewise_constant import PiecewiseConstant
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
