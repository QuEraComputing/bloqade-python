import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse

from bloqade.ir.visitor import BloqadeIRVisitor


class ScanChannels(BloqadeIRVisitor):
    def __init__(self):
        self.channels = None

    def visit_sequence_Sequence(self, node: sequence.Sequence):
        for lc, p in node.pulses.items():
            saved = dict() if self.channels is None else dict(self.channels)
            self.channels = saved.get(lc, {})
            self.visit(p)
            saved[lc] = self.channels
            self.channels = dict(saved)

    def visit_pulse_Pulse(self, node: pulse.Pulse):
        for fn, f in node.fields.items():
            saved = dict() if self.channels is None else dict(self.channels)
            self.channels = saved.get(fn, set())
            self.visit(f)
            saved[fn] = self.channels
            self.channels = dict(saved)

    def visit_field_Field(self, node: field.Field):
        self.channels = set() if self.channels is None else self.channels
        self.channels = set(node.drives.keys()) | self.channels

    def scan(self, node):
        self.visit(node)
        return self.channels
