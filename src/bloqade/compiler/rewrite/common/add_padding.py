import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.visitor import BloqadeIRTransformer


class AddPadding(BloqadeIRTransformer):
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
            drives[sm] = self.visit(
                self.add_waveform_padding(node.drives.get(sm), duration)
            )

        return field.Field(drives)

    def visit_waveform_Add(self, node: waveform.Add) -> waveform.Add:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if left.duration == right.duration:
            return left + right
        else:
            duration = left.duration.max(right.duration)
            return self.add_waveform_padding(
                left, duration
            ) + self.add_waveform_padding(right, duration)
