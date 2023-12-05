from bloqade.ir.visitor import BloqadeIRTransformer
from bloqade.ir import scalar
from bloqade.ir.control import pulse, sequence, field, waveform


def is_literal(expr):
    return isinstance(expr, scalar.Literal)


def is_negative(expr):
    return isinstance(expr, scalar.Negative)


def is_zero(expr):
    return isinstance(expr, scalar.Literal) and expr.value == 0


def is_one(expr):
    return isinstance(expr, scalar.Literal) and expr.value == 1


class Canonicalize(BloqadeIRTransformer):
    def minmax_canonicalize(self, op, exprs):
        new_exprs = set()
        for expr in exprs:
            if isinstance(expr, op):
                exprs = list(map(self.visit, expr.exprs))
                new_exprs.update(exprs)
            else:
                expr = self.visit(expr)
                new_exprs.add(expr)

        if len(new_exprs) > 1:
            return op(exprs=frozenset(new_exprs))
        else:
            (new_expr,) = new_exprs
            return new_expr

    def visit_scalar_Min(self, node: scalar.Min):
        return self.minmax_canonicalize(scalar.Min, node.exprs)

    def visit_scalar_Max(self, node: scalar.Max):
        return self.minmax_canonicalize(scalar.Max, node.exprs)

    def visit_scalar_Negative(self, node: scalar.Negative):
        expr = self.visit(node.expr)
        if isinstance(expr, scalar.Negative):
            return expr.expr
        elif is_literal(expr) and expr.value < 0:
            # literal expressions must be positive
            return scalar.Negative(expr=scalar.Literal(-expr.value))
        else:
            return scalar.Negative(expr=expr)

    def visit_scalar_Add(self, node: scalar.Add):
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        if lhs == rhs:
            return 2 * lhs
        elif is_zero(rhs):
            return rhs
        elif is_zero(lhs):
            return lhs
        elif is_literal(lhs) and is_literal(rhs):
            return scalar.Literal(lhs.value + rhs.value)
        elif is_negative(lhs) and is_negative(rhs):
            return self.visit(
                scalar.Negative(expr=scalar.Add(lhs=lhs.expr, rhs=rhs.expr))
            )
        elif (is_negative(lhs) and lhs.expr == rhs) or (
            is_negative(rhs) and rhs.expr == lhs
        ):
            return scalar.Literal(0)
        else:
            return scalar.Add(lhs=lhs, rhs=rhs)

    def visit_scalar_Mul(self, node: scalar.Mul):
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        if is_zero(lhs) or is_zero(rhs):
            return scalar.Literal(0)
        elif is_one(lhs):
            return rhs
        elif is_one(rhs):
            return lhs
        elif is_literal(lhs) and is_literal(rhs):
            return scalar.Literal(lhs.value * rhs.value)
        elif is_negative(lhs) and is_negative(rhs):
            return self.visit(scalar.Mul(lhs=lhs.expr, rhs=rhs.expr))
        elif is_negative(lhs) or is_negative(rhs):
            return self.visit(scalar.Negative(expr=scalar.Mul(lhs=lhs.expr, rhs=rhs)))
        else:
            return scalar.Mul(lhs=lhs, rhs=rhs)

    def visit_scalar_Div(self, node: scalar.Div):
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        if is_zero(lhs):
            return scalar.Literal(0)
        elif is_literal(lhs) and is_literal(rhs):
            return scalar.Literal(lhs.value / rhs.value)
        elif is_literal(rhs) and rhs.value == 1:
            return lhs
        elif is_negative(lhs) and is_negative(rhs):
            return self.visit(scalar.Div(lhs=lhs.expr, rhs=rhs.expr))
        elif is_negative(lhs) or is_negative(rhs):
            return self.visit(
                scalar.Negative(expr=self.visit(scalar.Div(lhs=lhs.expr, rhs=rhs)))
            )
        else:
            return scalar.Div(lhs=lhs, rhs=rhs)

    def visit_waveform_Append(self, node: waveform.Append):
        waveforms = []

        for sub_waveform in map(self.visit, node.waveforms):
            if sub_waveform.duration == scalar.Literal(0):
                continue
            elif isinstance(sub_waveform, waveform.Append):
                waveforms.extend(sub_waveform.waveforms)
            else:
                waveforms.append(sub_waveform)

        if len(waveforms) == 1:
            return waveforms[0]
        else:
            return waveform.Append(waveforms=waveforms)

    def visit_waveform_Add(self, node: waveform.Add):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if left == right:
            return waveform.Scale(2, waveform=left)
        elif left.duration == scalar.Literal(0):
            return right
        elif right.duration == scalar.Literal(0):
            return left
        else:
            return waveform.Add(left=left, right=right)

    def visit_waveform_Scale(self, node: waveform.Scale):
        factor = self.visit(node.factor)
        sub_waveform = self.visit(node.waveform)

        if is_zero(factor):
            return waveform.Constant(0, duration=sub_waveform.duration)
        elif is_one(factor):
            return sub_waveform
        elif isinstance(sub_waveform, waveform.Scale):
            return self.visit(
                waveform.Scale(
                    factor=factor * sub_waveform.factor, waveform=sub_waveform.waveform
                )
            )
        else:
            return waveform.Scale(factor=factor, waveform=sub_waveform)

    def visit_waveform_Slice(self, node: waveform.Slice):
        sub_waveform = self.visit(node.waveform)
        interval = self.visit(node.interval)

        if (
            interval.start == scalar.Literal(0)
            and interval.stop == sub_waveform.duration
        ):
            return sub_waveform
        elif isinstance(sub_waveform, waveform.Slice):
            start = node.start + sub_waveform.start
            stop = node.start + sub_waveform.stop

            interval = scalar.Interval(start=start, stop=stop)

            return self.visit(
                waveform.Slice(waveform=sub_waveform.waveform, interval=interval)
            )
        else:
            return waveform.Slice(waveform=sub_waveform, interval=interval)

    def visit_pulse_Slice(self, node: pulse.Slice):
        sub_pulse = self.visit(node.pulse)
        interval = self.visit(node.interval)

        if interval.start == scalar.Literal(0) and interval.stop == sub_pulse.duration:
            return sub_pulse
        elif isinstance(sub_pulse, pulse.Slice):
            start = node.start + sub_pulse.start
            stop = node.start + sub_pulse.stop

            interval = scalar.Interval(start=start, stop=stop)

            return self.visit(pulse.Slice(pulse=sub_pulse.pulse, interval=interval))
        else:
            return pulse.Slice(pulse=sub_pulse, interval=interval)

    def visit_pulse_Append(self, node: pulse.Append):
        pulses = []
        for p in map(self.visit, node.pulses):
            if p.duration == scalar.Literal(0):
                continue
            elif isinstance(p, pulse.Append):
                pulses.extend(p.pulses)
            else:
                pulses.append(p)

        if len(pulses) == 1:
            return pulses[0]
        else:
            return pulse.Append(pulses=pulses)

    def visit_sequence_Slice(self, node: sequence.Slice):
        sub_sequence = self.visit(node.sequence)
        interval = self.visit(node.interval)

        if (
            interval.start == scalar.Literal(0)
            and interval.stop == sub_sequence.duration
        ):
            return sub_sequence
        elif isinstance(sub_sequence, sequence.Slice):
            start = node.start + sub_sequence.start
            stop = node.start + sub_sequence.stop

            interval = scalar.Interval(start=start, stop=stop)

            return self.visit(
                sequence.Slice(sequence=sub_sequence.sequence, interval=interval)
            )
        else:
            return sequence.Slice(sequence=sub_sequence, interval=interval)

    def visit_sequence_Append(self, node: sequence.Append):
        sequences = []

        for sub_sequence in map(self.visit, node.sequences):
            if sub_sequence.duration == scalar.Literal(0):
                continue
            elif isinstance(sub_sequence, sequence.Append):
                sequences.extend(sub_sequence.sequences)
            else:
                sequences.append(sub_sequence)

        if len(sequences) == 1:
            return sequences[0]
        else:
            return sequence.Append(sequences=sequences)

    def visit_field_Field(self, node: field.Field):
        inv_drives = {}

        # map spatial modulations to waveforms
        for sm, wf in node.drives.items():
            wf = self.visit(wf)
            inv_drives[wf] = inv_drives.get(wf, []) + [sm]

        # merge spatial modulations with the same waveform
        for wf, sms in inv_drives.items():
            other_sms = []
            new_scaled_locations = field.ScaledLocations.create({})

            for sm in sms:  # merge scaled locations
                if isinstance(sm, field.ScaledLocations):
                    for loc, scale in sm.value.items():
                        new_scaled_locations[loc] = (
                            new_scaled_locations.get(loc, scalar.Literal(0)) + scale
                        )
                else:
                    other_sms.append(sm)

            if new_scaled_locations:
                # if there are any scaled locations,
                # add them to the list of spatial modulations
                other_sms.append(new_scaled_locations)

            inv_drives[wf] = other_sms

        drives = {sm: wf for wf, sms in inv_drives.items() for sm in sms}

        return field.Field(drives=drives)
