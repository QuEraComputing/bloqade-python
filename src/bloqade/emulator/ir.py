from pydantic.dataclasses import dataclass
from numpy.typing import Callable
from typing import Dict, Optional

import bloqade.ir.control.field as field
from bloqade.emulator.space import Space


@dataclass
class RabiDrive:
    amplitude: Dict[field.SpatialModulation, Callable[float, float]] = {}
    phase: Dict[field.SpatialModulation, Callable[float, float]] = {}


@dataclass
class LaserCoupling:
    detuning: Dict[field.SpatialModulation, Callable[float, float]] = {}
    rabi: RabiDrive = RabiDrive()


@dataclass
class EmulatorProgram:
    space: Space
    rydberg: Optional[LaserCoupling]
    hyperfine: Optional[LaserCoupling]
