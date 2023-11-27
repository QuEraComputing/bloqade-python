import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar


from bloqade.ir.visitor import BloqadeIRTransformer
from bloqade.analysis.common.scan_variables import ScanVariables
from bloqade.factory import piecewise_constant, piecewise_linear
from bisect import bisect_left
from decimal import Decimal
from beartype.typing import Union


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

    def get_times(self, wf: Union[waveform.Append, waveform.Waveform]):
        if isinstance(wf, waveform.Append):
            times = []
            time = Decimal("0")
            for wf in wf.waveforms:
                times.append(time)
                time += wf.duration()
            return times
        else:
            return [Decimal("0"), wf.duration()]

    def move_slice_into_append(
        self, wf: waveform.Append, start_time: Decimal, stop_time: Decimal
    ):
        if start_time == stop_time:
            return waveform.Constant(0, 0)

        times = self.get_times(wf)

        start_index = bisect_left(times[1:], start_time)
        stop_index = bisect_left(times[1:], stop_time)

        if start_index == stop_index:
            return wf.waveforms[start_index][start_time:stop_time]

        if start_time == times[start_index + 1]:
            wf_start = waveform.Constant(0, 0)
        else:
            start_time = start_time - times[start_index]

            wf_start = wf.waveforms[start_index][start_time:]

        if stop_time == times[stop_index + 1]:
            wf_stop = waveform.Constant(0, 0)
        else:
            stop_time = stop_time - times[stop_index]

            wf_stop = wf.waveforms[stop_index][:stop_time]

        return waveform.Append(
            [wf_start] + wf.waveforms[start_index + 1 : stop_index] + [wf_stop]
        )

    def move_add_inside_append(
        self,
        left: Union[waveform.Append, waveform.Waveform],
        right: Union[waveform.Append, waveform.Waveform],
    ):
        times = sorted(list(set(self.get_times(left) + self.get_times(right))))

        new_wf = None
        for start, stop in zip(times[:-1], times[1:]):
            next_wf = left[start:stop] + right[start:stop]

            if new_wf is None:
                new_wf = next_wf
            else:
                new_wf = new_wf.append(next_wf)

        return new_wf

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
        return self.visit(node)

    def visit_waveform_Scale(self, node: waveform.Scale) -> waveform.Waveform:
        wf = self.visit(node.waveform)

        if isinstance(wf, waveform.Append):
            wf = node.scalar * wf.waveforms[0]
            for next_wf in wf.waveforms[1:]:
                wf = wf.append(node.scalar * next_wf)

            return wf
        else:
            return node.scalar * wf

    def visit_waveform_Negative(self, node: waveform.Negative) -> waveform.Waveform:
        wf = self.visit(node.waveform)

        if isinstance(wf, waveform.Append):
            wf = -wf.waveforms[0]
            for next_wf in wf.waveforms[1:]:
                wf = wf.append(-next_wf)

            return wf
        else:
            return -wf

    def visit_waveform_Sample(self, node: waveform.Sample) -> waveform.Waveform:
        wf = self.visit(node.waveform)

        variable_scan_wf = ScanVariables().emit(wf)
        variable_scan_dt = ScanVariables().emit(node.dt)

        scalar_vars = variable_scan_wf.scalar_vars.union(variable_scan_dt.scalar_vars)

        if scalar_vars:
            return waveform.Sample(wf, node.interpolation, node.dt)

        times, values = node.samples()

        if node.interpolation is waveform.Interpolation.Linear:
            return piecewise_linear(times, values)
        elif node.interpolation is waveform.Interpolation.Constant:
            return piecewise_constant(times, values)

    def visit_waveform_Slice(self, node: waveform.Slice) -> waveform.Waveform:
        wf = self.visit(node.waveform)

        variable_scan_wf = ScanVariables().emit(wf)
        variable_scan_interval = ScanVariables().emit(node.interval)

        scalar_vars = variable_scan_wf.scalar_vars.union(
            variable_scan_interval.scalar_vars
        )

        # if waveform still has unassigned variables, we can't move the slice inside
        # the append so we just return the node
        if scalar_vars:
            return wf[node.interval.start : node.interval.stop]

        wf = self.visit(node.waveform)

        # if waveform is an append, we don't need to move the slice inside
        if not isinstance(wf, waveform.Append):
            return waveform.Slice(wf, node.interval)

        start = node.start()
        stop = node.stop()

        # no slice needed
        if start == Decimal("0") and stop == wf.duration():
            return wf

        # move slice inside append
        return self.move_slice_into_append(wf, start, stop)

    def visit_waveform_Add(self, node: waveform.Add) -> waveform.Add:
        # visit left and right side of add
        left = self.visit(node.left)
        right = self.visit(node.right)

        variable_scan_left = ScanVariables().emit(left)
        variable_scan_right = ScanVariables().emit(right)

        scalar_vars = variable_scan_left.scalar_vars.union(
            variable_scan_right.scalar_vars
        )

        # if waveforms still have unassigned variables, we can't move the add inside
        # the append so we just return the visited node
        if scalar_vars:
            return left + right

        # if either side is an append, we need to move the add inside the append
        if isinstance(left, waveform.Append) or isinstance(right, waveform.Append):
            return self.move_add_inside_append(left, right)

        return left + right
