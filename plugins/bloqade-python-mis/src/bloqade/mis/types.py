from dataclasses import dataclass
import numpy as np


@dataclass
class Geometry:
    positions: np.ndarray[np.float64, 2]


@dataclass
class MISProblem:
    geometry: Geometry
    
