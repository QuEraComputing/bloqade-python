from pydantic.dataclasses import dataclass
from bloqade.ir.scalar import Literal
from bloqade.ir.field import (
    SpatialModulation,
    GlobalModulation,
    ScaledLocations,
    RunTimeVector,
)
from bloqade.ir.pulse import FieldName
from bloqade.ir.field import Location
from typing import List, Optional
from bloqade.codegen.hardware.waveform import BaseCodeGen


@dataclass
class SpatialModulationCodeGen(BaseCodeGen):
    field_name: Optional[FieldName] = None
    lattice_site_coefficient: Optional[List[float]] = None

    def scan(self, ast: SpatialModulation):
        match ast:
            case GlobalModulation():
                self.lattice_site_coefficient = None
            case ScaledLocations(value):
                self.lattice_site_coefficient = []
                for atom_index in range(self.n_atom):
                    expr = value.get(Location(atom_index), Literal(0.0))
                    self.lattice_site_coefficient.append(
                        expr(**self.assignments)
                    )
            case RunTimeVector(name):
                lattice_site_coefficient = self.assignments[name]
                if len(lattice_site_coefficient) != self.n_atoms:
                    raise ValueError(
                        f"Number of elements in {name} must be equal to the number of atoms {self.n_atoms}"
                    )
                self.lattice_site_coefficient.extend(lattice_site_coefficient)

    def emit(self, ast: SpatialModulation):
        self.scan(ast)
        return self.lattice_site_coefficient
