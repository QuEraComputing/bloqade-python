import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse


from pydantic.dataclasses import dataclass
from beartype.typing import FrozenSet
from bloqade.ir.visitor import BloqadeIRVisitor


@dataclass(frozen=True)
class Channels:
    level_couplings: FrozenSet[sequence.LevelCoupling]
    field_names: FrozenSet[pulse.FieldName]
    spatial_modulations: FrozenSet[field.SpatialModulation]


class ScanChannels(BloqadeIRVisitor):
    def visit_sequence_Sequence(self, node: sequence.Sequence):
        for lc in node.pulses:
            self.level_couplings.add(lc)
            self.visit(node.pulses[lc])

    def visit_pulse_Pulse(self, node: pulse.Pulse):
        for fn in node.fields:
            self.field_names.add(fn)
            self.visit(node.fields[fn])

    def visit_field_Field(self, node: field.Field):
        for sm in node.drives:
            self.spatial_modulations.add(sm)

    def scan(self, node) -> Channels:
        self.level_couplings = set()
        self.field_names = set()
        self.spatial_modulations = set()

        self.visit(node)
        return Channels(
            level_couplings=frozenset(self.level_couplings),
            field_names=frozenset(self.field_names),
            spatial_modulations=frozenset(self.spatial_modulations),
        )
