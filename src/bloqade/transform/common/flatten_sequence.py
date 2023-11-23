import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.visitor import BloqadeIRTransformer

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
        if diff_duration == scalar.Literal(0):
            return wf

        if isinstance(wf, waveform.AlignedWaveform):
            raise NotImplementedError("AlignedWaveform not implemented yet")
            # if isinstance(wf.value, waveform.Side):
            #     value = scalar.var(f"__record_value_{hash(wf) ^ hash(wf.value)}__")
            #     wf = wf.record(value, wf.value)
            #     padding = waveform.Constant(value, diff_duration)
            # else:
            #     value = wf.value

            # padding = waveform.Constant(wf.value, diff_duration)

            # if wf.alignment is waveform.Alignment.Left:
            #     return wf.append(padding)
            # else:
            #     return padding.append(wf)
        else:
            padding = waveform.Constant(0, diff_duration)
            return wf.append(padding)

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

    #######################
    # Visitor definitions #
    #######################

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> sequence.Sequence:
        pulses = {}
        for lc, field_names in self.level_couplings.items():
            self.field_names = field_names

            if lc in node.pulses:
                p = self.visit(node.pulses[lc])
            else:
                p = self.get_empty_pulse(node.duration)

            diff_duration = node.duration - p.duration

            if diff_duration != scalar.Literal(0):
                p = p.append(self.get_empty_pulse(diff_duration))

            pulses[lc] = p

        return sequence.Sequence(pulses)

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> pulse.Pulse:
        self.pulse_duration = node.duration

        fields = {}
        for fn, spatial_modulations in self.field_names.items():
            self.spatial_modulations = spatial_modulations
            if fn in node.fields:
                fields[fn] = self.visit(node.fields[fn])
            else:  # no need to visit empty field
                fields[fn] = self.get_empty_field(self.pulse_duration)

        return pulse.Pulse(fields)

    def visit_field_Field(self, node: field.Field) -> field.Field:
        duration = (
            self.pulse_duration if self.pulse_duration is not None else node.duration
        )
        drives = {}

        for sm in self.spatial_modulations:
            drives[sm] = self.add_waveform_padding(node.drives.get(sm), duration)

        return field.Field(drives)


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
