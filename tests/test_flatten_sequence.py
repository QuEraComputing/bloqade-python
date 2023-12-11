import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence
from bloqade.ir.scalar import var

from bloqade.analysis.common.scan_channels import ScanChannels
from bloqade.rewrite.common.flatten import FlattenCircuit
from bloqade.rewrite.common.add_padding import AddPadding
from bloqade import tree_depth

tree_depth(30)


def test_flatten_pulses_simple():
    wf1 = waveform.Constant("v1", "t1")
    wf2 = waveform.Constant("v2", "t2")

    sm1 = field.UniformModulation()
    sm2 = field.RunTimeVector("mask1")

    f1 = field.Field({sm1: wf1})
    f2 = field.Field({sm2: wf2})

    p1 = pulse.Pulse({pulse.rabi.amplitude: f1})
    p2 = pulse.Pulse({pulse.rabi.phase: f2})

    t = var("t")
    p_test = p1.append(p2)[:t]
    interval = p_test.interval

    field_names = ScanChannels().scan(p_test)

    duration_1 = p1.duration
    duration_2 = p2.duration

    p_filled_expected = pulse.Slice(
        pulse.Append(
            [
                pulse.Pulse(
                    {
                        pulse.rabi.amplitude: f1,
                        pulse.rabi.phase: field.Field(
                            {sm2: waveform.Constant(0, duration_1)}
                        ),
                    }
                ),
                pulse.Pulse(
                    {
                        pulse.rabi.amplitude: field.Field(
                            {sm1: waveform.Constant(0, duration_2)}
                        ),
                        pulse.rabi.phase: f2,
                    }
                ),
            ]
        ),
        interval,
    )

    p_flattened_expected = pulse.Pulse(
        {
            pulse.rabi.amplitude: field.Field(
                {
                    sm1: wf1.append(waveform.Constant(0, duration_2))[:t],
                }
            ),
            pulse.rabi.phase: field.Field(
                {sm2: waveform.Constant(0, duration_1).append(wf2)[:t]}
            ),
        }
    )

    p_filled = AddPadding(field_names=field_names).visit(p_test)
    p_flattened = FlattenCircuit(field_names=field_names).visit(p_filled)

    assert p_filled_expected == p_filled
    assert p_flattened_expected == p_flattened


def test_flatten_pulses_complex():
    wf1 = waveform.Constant("v1", "t1")
    wf2 = waveform.Constant("v2", "t2")
    wf3 = waveform.Constant("v3", "t3")
    wf4 = waveform.Constant("v4", "t4")

    sm1 = field.UniformModulation()
    sm2 = field.RunTimeVector("mask1")
    sm3 = field.AssignedRunTimeVector("mask2", list(range(4)))
    sm4 = field.ScaledLocations.create(
        {field.Location(0): "m0", field.Location(2): "m2"}
    )

    f1 = field.Field({sm1: wf1})
    f2 = field.Field({sm2: wf2})
    f3 = field.Field({sm3: wf3, sm4: wf4})

    p1 = pulse.Pulse({pulse.rabi.amplitude: f1})
    p2 = pulse.Pulse({pulse.rabi.phase: f2, pulse.detuning: f3})

    t = var("t")
    p_test = p1.append(p2)[:t]
    interval = p_test.interval

    field_names = ScanChannels().scan(p_test)

    duration_1 = p1.duration
    duration_2 = p2.duration

    f2_padded = field.Field(
        {
            sm: wf.append(waveform.Constant(0, duration_2 - wf.duration))
            for sm, wf in f2.drives.items()
        }
    )
    f3_padded = field.Field(
        {
            sm: wf.append(waveform.Constant(0, duration_2 - wf.duration))
            for sm, wf in f3.drives.items()
        }
    )

    p_filled_expected = pulse.Slice(
        pulse.Append(
            [
                pulse.Pulse(
                    {
                        pulse.rabi.amplitude: f1,
                        pulse.rabi.phase: field.Field(
                            {
                                sm: waveform.Constant(0, duration_1)
                                for sm in f2.drives.keys()
                            }
                        ),
                        pulse.detuning: field.Field(
                            {
                                sm: waveform.Constant(0, duration_1)
                                for sm in f3.drives.keys()
                            }
                        ),
                    }
                ),
                pulse.Pulse(
                    {
                        pulse.rabi.amplitude: field.Field(
                            {sm1: waveform.Constant(0, duration_2)}
                        ),
                        pulse.rabi.phase: f2_padded,
                        pulse.detuning: f3_padded,
                    }
                ),
            ]
        ),
        interval,
    )

    p_flattened_expected = pulse.Pulse(
        {
            pulse.rabi.amplitude: field.Field(
                {sm1: wf1.append(waveform.Constant(0, duration_2))[:t]}
            ),
            pulse.rabi.phase: field.Field(
                {
                    sm: waveform.Constant(0, duration_1).append(wf)[:t]
                    for sm, wf in f2_padded.drives.items()
                }
            ),
            pulse.detuning: field.Field(
                {
                    sm: waveform.Constant(0, duration_1).append(wf)[:t]
                    for sm, wf in f3_padded.drives.items()
                }
            ),
        }
    )

    p_filled = AddPadding(field_names=field_names).visit(p_test)
    p_flattened = FlattenCircuit(field_names=field_names).visit(p_filled)

    assert p_filled_expected == p_filled
    assert p_flattened_expected == p_flattened


def test_flatten_sequence_simple():
    wf1 = waveform.Constant("v1", "t1")
    wf2 = waveform.Constant("v2", "t2")

    sm1 = field.UniformModulation()
    sm2 = field.RunTimeVector("mask1")

    f1 = field.Field({sm1: wf1})
    f2 = field.Field({sm2: wf2})

    p1 = pulse.Pulse({pulse.rabi.amplitude: f1})
    p2 = pulse.Pulse({pulse.rabi.phase: f2})

    s1 = sequence.Sequence({sequence.hyperfine: p1})
    s2 = sequence.Sequence({sequence.rydberg: p2})

    t = var("t")
    s_test = s1.append(s2)[:t]

    interval = s_test.interval

    p2_1 = pulse.Pulse(
        {pulse.rabi.phase: field.Field({sm2: waveform.Constant(0, p1.duration)})}
    )
    p1_2 = pulse.Pulse(
        {pulse.rabi.amplitude: field.Field({sm1: waveform.Constant(0, p2.duration)})}
    )

    s_filled_expected = sequence.Slice(
        interval=interval,
        sequence=sequence.Append(
            [
                sequence.Sequence({sequence.hyperfine: p1, sequence.rydberg: p2_1}),
                sequence.Sequence({sequence.hyperfine: p1_2, sequence.rydberg: p2}),
            ]
        ),
    )

    s_flattened_expected = sequence.Sequence(
        {
            sequence.hyperfine: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {sm1: wf1.append(waveform.Constant(0, p2.duration))[:t]}
                    )
                },
            ),
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.phase: field.Field(
                        {sm2: waveform.Constant(0, p1.duration).append(wf2)[:t]}
                    )
                }
            ),
        }
    )

    level_couplings = ScanChannels().scan(s_test)
    s_filled = AddPadding(level_couplings=level_couplings).visit(s_test)
    s_flattened = FlattenCircuit(level_couplings=level_couplings).visit(s_filled)
    print(s_filled_expected)
    print(s_filled)
    assert s_filled_expected == s_filled
    assert s_flattened_expected == s_flattened


def test_flatten_sequence_simple_2():
    wf1 = waveform.Constant("v1", "t1")
    wf2 = waveform.Constant("v2", "t2")

    sm1 = field.UniformModulation()
    sm2 = field.RunTimeVector("mask1")

    f1 = field.Field({sm1: wf1})
    f2 = field.Field({sm2: wf2})

    p1 = pulse.Pulse({pulse.rabi.amplitude: f1})
    p2 = pulse.Pulse({pulse.rabi.phase: f2})

    s_test = sequence.Sequence({sequence.hyperfine: p1, sequence.rydberg: p2})

    duration = s_test.duration

    p1_padding = pulse.Pulse(
        {
            pulse.rabi.amplitude: field.Field(
                {sm1: waveform.Constant(0, duration - p1.duration)}
            )
        }
    )
    p2_padding = pulse.Pulse(
        {
            pulse.rabi.phase: field.Field(
                {sm2: waveform.Constant(0, duration - p2.duration)}
            )
        }
    )

    s_filled_expected = sequence.Sequence(
        {
            sequence.hyperfine: p1.append(p1_padding),
            sequence.rydberg: p2.append(p2_padding),
        }
    )

    s_flattened_expected = sequence.Sequence(
        {
            sequence.hyperfine: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {sm1: wf1.append(waveform.Constant(0, duration - p1.duration))}
                    )
                },
            ),
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.phase: field.Field(
                        {sm2: wf2.append(waveform.Constant(0, duration - p2.duration))}
                    )
                }
            ),
        }
    )

    level_couplings = ScanChannels().scan(s_test)
    s_filled = AddPadding(level_couplings=level_couplings).visit(s_test)
    s_flattened = FlattenCircuit(level_couplings=level_couplings).visit(s_filled)

    assert s_filled_expected == s_filled
    assert s_flattened_expected == s_flattened
