import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
from bloqade.ir.visitor import BloqadeIRTransformer


class FlattenBloqadeIR(BloqadeIRTransformer):
    # every visitor for sequence returns a Sequence

    def __init__(
        self,
        level_couplings=None,
        field_names=None,
        spatial_modulations=None,
    ):
        self.level_couplings = level_couplings
        self.field_names = field_names
        self.spatial_modulations = spatial_modulations
        self.duration = None

    #######################
    # Visitor definitions #
    #######################

    def visit_sequence_Append(self, node: sequence.Append) -> sequence.Sequence:
        seqs = list(map(self.visit, node.sequences))

        pulses = {}
        for lc in self.level_couplings:
            for s in seqs:
                p = s.pulses[lc]
                pulses[lc] = pulses[lc].append(p) if lc in pulses else p

        return self.visit(sequence.Sequence(pulses))

    def visit_sequence_Slice(self, node: sequence.Slice) -> sequence.Sequence:
        seq = self.visit(node.sequence)
        interval = node.interval

        pulses = {}

        for lc in self.level_couplings:
            p = seq.pulses[lc]
            pulses[lc] = p[interval.start : interval.stop]

        return self.visit(sequence.Sequence(pulses))

    def visit_sequence_NamedSequence(
        self, node: sequence.NamedSequence
    ) -> sequence.Sequence:
        return self.visit(node.sequence)

    def visit_pulse_Slice(self, node: pulse.Slice) -> pulse.Pulse:
        p = self.visit(node.pulse)
        interval = node.interval

        fields = {}

        for fn, f in p.fields.items():
            drives = {}
            for sm, wf in f.drives.items():
                drives[sm] = wf[interval.start : interval.stop]

            fields[fn] = field.Field(drives)

        return pulse.Pulse(fields)

    def visit_pulse_Append(self, node: pulse.Append) -> pulse.Pulse:
        pulses = list(map(self.visit, node.pulses))
        fields = dict(pulses[0].fields)

        for p in pulses[1:]:
            for fn, f in p.fields.items():
                for sm, wf in f.drives.items():
                    curr_wf = fields[fn].drives[sm]
                    fields[fn].drives[sm] = curr_wf.append(wf)

        return pulse.Pulse(fields)

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> pulse.Pulse:
        return self.visit(node)
