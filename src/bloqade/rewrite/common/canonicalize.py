from bloqade.ir.visitor import BloqadeIRTransformer
from bloqade.ir import scalar
from bloqade.ir.control import pulse, sequence, field, waveform


def is_literal(expr):
    return isinstance(expr, scalar.Literal)


def is_negative(expr):
    return isinstance(expr, scalar.Negative) or isinstance(expr, waveform.Negative)


def is_zero(expr):
    return isinstance(expr, scalar.Literal) and expr.value == 0


def is_one(expr):
    return isinstance(expr, scalar.Literal) and expr.value == 1


def is_scaled_waveform(expr):
    return isinstance(expr, waveform.Scale)


def is_constant_waveform(expr):
    return isinstance(expr, waveform.Constant)


class Canonicalizer(BloqadeIRTransformer):
    def minmax_canonicalize(self, op, exprs):
        new_exprs = set()
        new_literals = set()

        for expr in exprs:
            if isinstance(expr, op):
                exprs = list(map(self.visit, expr.exprs))
                new_exprs.update(expr for expr in exprs if not is_literal(expr))
                new_literals.update(expr for expr in exprs if is_literal(expr))
            else:
                expr = self.visit(expr)
                if is_literal(expr):
                    new_literals.add(expr)
                else:
                    new_exprs.add(expr)

        if new_literals:
            if len(new_literals) > 1:
                minmax = min if op == scalar.Min else max
                new_literal = scalar.Literal(
                    minmax(*[ele.value for ele in new_literals])
                )
            else:
                new_literal = new_literals.pop()

            new_exprs.add(new_literal)

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
        if is_negative(expr):
            return expr.expr
        elif is_literal(expr):
            return scalar.Literal(-expr.value)
        else:  # only apply negative to literals
            return scalar.Negative(expr=expr)

    def visit_scalar_Add(self, node: scalar.Add):
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        if lhs == rhs:
            return 2 * lhs
        elif is_zero(rhs):
            return lhs
        elif is_zero(lhs):
            return rhs
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
        elif is_negative(lhs):
            return self.visit(scalar.Negative(expr=scalar.Mul(lhs=lhs.expr, rhs=rhs)))
        elif is_negative(rhs):
            return self.visit(scalar.Negative(expr=scalar.Mul(lhs=lhs, rhs=rhs.expr)))
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
        elif is_negative(lhs):
            return self.visit(
                scalar.Negative(expr=self.visit(scalar.Div(lhs=lhs.expr, rhs=rhs)))
            )
        elif is_negative(rhs):
            return self.visit(
                scalar.Negative(expr=self.visit(scalar.Div(lhs=lhs, rhs=rhs.expr)))
            )
        else:
            return scalar.Div(lhs=lhs, rhs=rhs)

    ########################################
    #    Waveform Canonicalization Pass    #
    ########################################

    def visit_waveform_Append(self, node: waveform.Append):
        waveforms_pass_one = []

        # flatten nested append nodes
        for sub_waveform in map(self.visit, node.waveforms):
            if sub_waveform.duration == scalar.Literal(0):
                continue
            elif isinstance(sub_waveform, waveform.Append):
                waveforms_pass_one.extend(sub_waveform.waveforms)
            else:
                waveforms_pass_one.append(sub_waveform)

        # combine adjacent constant waveforms if possible
        waveforms_pass_two = [waveforms_pass_one[0]]
        for next_wf in waveforms_pass_one[1:]:
            last_wf = waveforms_pass_two.pop()
            if (
                is_constant_waveform(last_wf)
                and is_constant_waveform(next_wf)
                and last_wf.value == next_wf.value
            ):
                new_duration = self.visit(last_wf.duration + next_wf.duration)
                waveforms_pass_two.append(
                    waveform.Constant(value=last_wf.value, duration=new_duration)
                )
            else:
                waveforms_pass_two.append(last_wf)
                waveforms_pass_two.append(next_wf)

        # if there is only one waveform, return it
        if len(waveforms_pass_two) == 1:
            return waveforms_pass_two[0]
        else:
            return waveform.Append(waveforms=waveforms_pass_two)

    def visit_waveform_Add(self, node: waveform.Add):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if left == right:
            return self.visit(waveform.Scale(2, waveform=left))
        elif is_zero(left.duration) or (
            is_constant_waveform(left) and is_zero(left.value)
        ):
            return right
        elif is_zero(right.duration) or (
            is_constant_waveform(right) and is_zero(right.value)
        ):
            return left
        elif (
            is_constant_waveform(left)
            and is_constant_waveform(right)
            and (left.duration == right.duration)
        ):
            return self.visit(
                waveform.Constant(
                    value=left.value + right.value, duration=left.duration
                )
            )
        elif (
            is_scaled_waveform(left)
            and is_scaled_waveform(right)
            and left.scalar == right.scalar
        ):
            new_waveform = left.waveform + right.waveform
            return self.visit(waveform.Scale(scalar=left.scalar, waveform=new_waveform))
        elif (
            is_scaled_waveform(left)
            and is_scaled_waveform(right)
            and left.waveform == right.waveform
        ):
            new_scalar = left.scalar + right.scalar
            return self.visit(waveform.Scale(scalar=new_scalar, waveform=left.waveform))
        elif is_scaled_waveform(left) and left.waveform == right:
            return self.visit(
                waveform.Scale(scalar=left.scalar + 1, waveform=left.waveform)
            )
        elif is_scaled_waveform(right) and right.waveform == left:
            return self.visit(
                waveform.Scale(scalar=right.scalar + 1, waveform=right.waveform)
            )
        else:
            return waveform.Add(left=left, right=right)

    def visit_waveform_Scale(self, node: waveform.Scale):
        scale = self.visit(node.scalar)
        sub_waveform = self.visit(node.waveform)

        if is_zero(scale):
            return waveform.Constant(0, duration=sub_waveform.duration)
        elif is_one(scale):
            return sub_waveform
        elif is_scaled_waveform(sub_waveform):
            return waveform.Scale(
                scalar=scale * sub_waveform.scalar, waveform=sub_waveform.waveform
            )

        elif is_constant_waveform(sub_waveform):
            return waveform.Constant(
                value=scale * sub_waveform.value, duration=sub_waveform.duration
            )
        else:
            return waveform.Scale(scalar=scale, waveform=sub_waveform)

    def visit_waveform_Slice(self, node: waveform.Slice):
        sub_waveform = self.visit(node.waveform)
        interval = self.visit(node.interval)

        if (
            interval.start == scalar.Literal(0)
            and interval.stop == sub_waveform.duration
        ):
            return sub_waveform
        elif is_scaled_waveform(sub_waveform):
            new_waveform = waveform.Slice(
                waveform=sub_waveform.waveform, interval=interval
            )
            return waveform.Scale(
                scalar=sub_waveform.scalar,
                waveform=new_waveform,
            )

        elif is_negative(sub_waveform):
            return waveform.Negative(
                waveform.Slice(waveform=sub_waveform.waveform, interval=interval)
            )

        else:
            return waveform.Slice(waveform=sub_waveform, interval=interval)

    def visit_waveform_Negative(self, node: waveform.Negative):
        sub_waveform = self.visit(node.waveform)

        if isinstance(sub_waveform, waveform.Negative):
            return sub_waveform.waveform
        elif is_constant_waveform(sub_waveform):
            new_value = -sub_waveform.value
            return waveform.Constant(
                value=new_value,
                duration=sub_waveform.duration,
            )
        elif is_scaled_waveform(sub_waveform) and is_negative(sub_waveform.scalar):
            new_scalar = -sub_waveform.scalar
            return waveform.Scale(
                scalar=new_scalar,
                waveform=sub_waveform.waveform,
            )
        else:
            return waveform.Negative(waveform=sub_waveform)

    ########################################
    #    Field Canonicalization Pass       #
    ########################################

    def visit_field_Field(self, node: field.Field):
        inv_drives = {}

        # map spatial modulations to waveforms
        for sm, wf in node.drives.items():
            wf = self.visit(wf)
            inv_drives[wf] = inv_drives.get(wf, []) + [sm]

        # merge spatial modulations with the same waveform
        for wf, sms in inv_drives.items():
            other_sms = []
            new_scaled_locations = {}

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
                other_sms.append(field.ScaledLocations.create(new_scaled_locations))

            inv_drives[wf] = other_sms

        drives = {sm: wf for wf, sms in inv_drives.items() for sm in sms}

        return field.Field(drives=drives)

    ########################################
    #    Pulse Canonicalization Pass       #
    ########################################

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

    ########################################
    #    Sequence Canonicalization Pass    #
    ########################################

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
