import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.visitor import BloqadeIRTransformer
from bloqade.analysis.common.scan_channels import ScanChannels
from beartype.typing import Any

# Passes for compiling to hardware
# 1. Scan all spatial modulations, validate here
# 2. Insert zero waveform in the explicit time intervals missing a waveform
# 3. Flatten all sequences to a single sequence by moving slices/appends to waveform
#    level
# 4. Assign variables, validate here
# 5. Move the waveform slices into appends
# 5. Validate waveform to be hardware compatible
# 6. generate IR for hardware


class FillMissingWaveforms(BloqadeIRTransformer):
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

    def add_waveform_padding(self, wf, duration):
        if wf is None:
            return waveform.Constant(0, duration)

        diff_duration = duration - wf.duration

        if diff_duration == 0:
            return wf

        if isinstance(wf, waveform.AlignedWaveform):
            if isinstance(wf.value, waveform.Side):
                value = scalar.var(f"__record_value_{hash(wf) ^ hash(wf.value)}__")
                wf = wf.record(value, wf.value)
                padding = waveform.Constant(value, diff_duration)
            else:
                value = wf.value

            padding = waveform.Constant(wf.value, diff_duration)

            if wf.alignment is waveform.Alignment.Left:
                return wf.append(padding)
            else:
                return padding.append(wf)
        else:
            padding = waveform.Constant(0, diff_duration)
            return wf.append(padding)

    def add_pulse_padding(self, p, duration):
        if p is None:
            return self.get_empty_pulse(duration)

        diff_duration = duration - p.duration

        if diff_duration == 0:
            return p

        return p.append(self.get_empty_pulse(diff_duration))

    def get_empty_field(self, duration):
        empty_wf = waveform.Constant(0, duration)
        empty_f = field.Field({sm: empty_wf for sm in self.spatial_modulations})
        return empty_f

    def get_empty_pulse(self, duration):
        fields = {}
        for fn, spatial_modulations in self.field_names.items():
            self.spatial_modulations = spatial_modulations
            fields[fn] = self.get_empty_field(duration)

        return pulse.Pulse(fields)

    def _scan_channels(self, node: Any):
        # scan for channels in all nodes
        # but do not override the channels if already set
        if isinstance(node, sequence.SequenceExpr):
            self.level_couplings = (
                ScanChannels().scan(node)
                if self.level_couplings is None
                else self.level_couplings
            )
        elif isinstance(node, pulse.PulseExpr):
            self.field_names = (
                ScanChannels().scan(node)
                if self.field_names is None
                else self.field_names
            )
        elif isinstance(node, field.Field):
            self.spatial_modulations = (
                ScanChannels().scan(node)
                if self.spatial_modulations is None
                else self.spatial_modulations
            )

    #######################
    # Visitor definitions #
    #######################

    def visit(self, node: Any) -> Any:
        self._scan_channels(node)

        return super().visit(node)

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> sequence.Sequence:
        self.duration = node.duration  # this is always the case

        pulses = {}
        for lc, field_names in self.level_couplings.items():
            self.field_names = field_names

            if lc in node.pulses:
                pulses[lc] = self.visit(node.pulses[lc])
            else:
                pulses[lc] = self.get_empty_pulse(self.duration)

        return sequence.Sequence(pulses)

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> pulse.Pulse:
        self.duration = node.duration if self.duration is None else self.duration

        fields = {}
        for fn, spatial_modulations in self.field_names.items():
            self.spatial_modulations = spatial_modulations
            if fn in node.fields:
                fields[fn] = self.visit(node.fields[fn])
            else:  # no need to visit empty field
                fields[fn] = self.get_empty_field(self.duration)

        return pulse.Pulse(fields)

    def visit_field_Field(self, node: field.Field) -> field.Field:
        self.duration = node.duration if self.duration is None else self.duration

        drives = {}

        for sm in self.spatial_modulations:
            drives[sm] = self.add_waveform_padding(node.drives.get(sm), self.duration)

        return field.Field(drives)


class FlattenBloqadeIR(BloqadeIRTransformer):
    # every visitor for sequence returns a Sequence

    def __init__(
        self,
        level_couplings=None,
        field_names=None,
        spatial_modulations=None,
        duration=None,
    ):
        self.level_couplings = level_couplings
        self.field_names = field_names
        self.spatial_modulations = spatial_modulations
        self.duration = duration

    def _scan_channels(self, node: Any):
        # scan for channels in all nodes
        # but do not override the channels if already set
        if isinstance(node, sequence.SequenceExpr):
            self.level_couplings = (
                ScanChannels().scan(node)
                if self.level_couplings is None
                else self.level_couplings
            )
        elif isinstance(node, pulse.PulseExpr):
            self.field_names = (
                ScanChannels().scan(node)
                if self.field_names is None
                else self.field_names
            )
        elif isinstance(node, field.Field):
            self.spatial_modulations = (
                ScanChannels().scan(node)
                if self.spatial_modulations is None
                else self.spatial_modulations
            )

    #######################
    # Visitor definitions #
    #######################

    def visit(self, node: Any) -> Any:
        self._scan_channels(node)
        return super().visit(node)

    def visit_sequence_Append(self, node: sequence.Append) -> sequence.Sequence:
        seqs = [self.visit(s) for s in node.sequences]

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

        return self.visit(pulse.Pulse(fields))

    def visit_pulse_Append(self, node: pulse.Append) -> pulse.Pulse:
        pulses = list(map(self.visit, node.pulses))

        fields = dict(pulses[0].fields)

        for p in pulses[1:]:
            for fn, f in p.fields.items():
                for sm, wf in f.drives.items():
                    curr_wf = fields[fn].drives[sm]
                    fields[fn].drives[sm] = curr_wf.append(wf)

        return self.visit(pulse.Pulse(fields))

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> pulse.Pulse:
        return self.visit(node.pulse)
