from pydantic.dataclasses import dataclass
from bloqade.ir.sequence import Sequence, 
from typing import Dict
from bloqade.codegen.hardware.pulse import PulseCodeGen
from quera_ahs_utils.quera_ir.task_specification import RydbergHamiltonian

@dataclass
class SequenceCodeGen(PulseCodeGen):
    
    # override dataclass __init__ to give required arguments for codegen
    def __init__(self, variable_reference: Dict[str, float], n_atoms: int):
        super().__init__(variable_reference=variable_reference, n_atoms=n_atoms)
    

    def scan_hardware(self, ast: Sequence):
        raise NotImplementedError
    
    def emit_hardware(self, ast: Sequence):
        raise NotImplementedError
    
    
