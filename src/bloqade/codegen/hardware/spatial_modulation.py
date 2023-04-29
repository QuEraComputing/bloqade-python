from pydantic.dataclasses import dataclass
from bloqade.ir.field import SpatialModulation
from typing import List, Dict
from bloqade.codegen.hardware.waveform import WaveformCodeGen

@dataclass
class SpatialModulationCodeGen(WaveformCodeGen):
    n_atoms: int = 1
    variable_reference: Dict[str, float] = {}
    lattice_site_coefficient: List[float] = []
    
    def scan(self, ast: SpatialModulation):
        raise NotImplementedError
