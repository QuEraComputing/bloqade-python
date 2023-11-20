import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse

from pydantic.dataclasses import dataclass
from pydantic import Field
from beartype.typing import Any, FrozenSet
from bloqade.ir.visitor import BloqadeIRVisitor


@dataclass(frozen=True)
class Channels:
    level_couplings: FrozenSet[sequence.LevelCoupling] = Field(
        default_factory=frozenset
    )
    field_names: FrozenSet[pulse.FieldName] = Field(default_factory=frozenset)
    spatial_modulations: FrozenSet[field.SpatialModulation] = Field(
        default_factory=frozenset
    )


class ScanChannels(BloqadeIRVisitor):
    def __init__(self):
        self.level_couplings = set()
        self.field_names = set()
        self.spatial_modulations = set()

    def generic_visit(self, node: Any) -> Any:
        if isinstance(node, field.SpatialModulation):
            self.spatial_modulations.add(node)
        elif isinstance(node, pulse.FieldName):
            self.field_names.add(node)
        elif isinstance(node, sequence.LevelCoupling):
            self.level_couplings.add(node)
        else:
            super().generic_visit(node)

    def scan(self, node) -> Channels:
        self.visit(node)
        return Channels(
            level_couplings=frozenset(self.level_couplings),
            field_names=frozenset(self.field_names),
            spatial_modulations=frozenset(self.spatial_modulations),
        )
