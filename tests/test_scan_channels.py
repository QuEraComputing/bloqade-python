import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence

# from bloqade.ir.scalar import var

from bloqade.analysis.common.scan_channels import ScanChannels, Channels


def test_scan_channels():
    wf1 = waveform.Constant("v1", "t1")
    wf2 = waveform.Constant("v2", "t2")
    wf3 = waveform.Constant("v3", "t3")
    wf4 = waveform.Constant(4.0, "t4")

    sm1 = field.UniformModulation()
    sm2 = field.RunTimeVector("mask1")
    sm3 = field.AssignedRunTimeVector("mask2", list(range(4)))
    sm4 = field.ScaledLocations({field.Location(0): "m0", field.Location(2): "m2"})

    f1 = field.Field({sm1: wf1, sm2: wf2})
    f2 = field.Field({sm3: wf3, sm4: wf4})
    f3 = field.Field({sm1: wf2, sm2: wf3})
    f4 = field.Field({sm3: wf4, sm4: wf1, sm1: wf2})

    assert ScanChannels().scan(f1) == Channels(
        spatial_modulations=frozenset({sm1, sm2})
    )
    assert ScanChannels().scan(f2) == Channels(
        spatial_modulations=frozenset({sm3, sm4})
    )
    assert ScanChannels().scan(f3) == Channels(
        spatial_modulations=frozenset({sm1, sm2})
    )
    assert ScanChannels().scan(f4) == Channels(
        spatial_modulations=frozenset({sm3, sm4, sm1})
    )

    p1 = pulse.Pulse({pulse.rabi.amplitude: f2, pulse.rabi.phase: f3})
    p2 = pulse.Pulse({pulse.detuning: f4, pulse.rabi.amplitude: f1})
    p3 = p1.append(p2)
    # p4 = p3[:var("t")]
    # p5 = p4.append(p1)

    assert ScanChannels().scan(p1) == Channels(
        spatial_modulations=frozenset({sm1, sm2, sm3, sm4}),
        field_names=frozenset({pulse.rabi.amplitude, pulse.rabi.phase}),
    )
    assert ScanChannels().scan(p2) == Channels(
        spatial_modulations=frozenset({sm1, sm2, sm3, sm4}),
        field_names=frozenset({pulse.detuning, pulse.rabi.amplitude}),
    )
    assert ScanChannels().scan(p3) == Channels(
        spatial_modulations=frozenset({sm1, sm2, sm3, sm4}),
        field_names=frozenset({pulse.detuning, pulse.rabi.amplitude, pulse.rabi.phase}),
    )

    s1 = sequence.Sequence({sequence.hyperfine: p1})
    s2 = sequence.Sequence({sequence.rydberg: p2})
    s3 = s1.append(s2)
    # s4 = s3[:var("t")]
    # s5 = s4.append(s1)

    assert ScanChannels().scan(s1) == Channels(
        spatial_modulations=frozenset({sm1, sm2, sm3, sm4}),
        field_names=frozenset({pulse.rabi.amplitude, pulse.rabi.phase}),
        level_couplings=frozenset({sequence.hyperfine}),
    )
    assert ScanChannels().scan(s2) == Channels(
        spatial_modulations=frozenset({sm1, sm2, sm3, sm4}),
        field_names=frozenset({pulse.detuning, pulse.rabi.amplitude}),
        level_couplings=frozenset({sequence.rydberg}),
    )
    assert ScanChannels().scan(s3) == Channels(
        spatial_modulations=frozenset({sm1, sm2, sm3, sm4}),
        field_names=frozenset({pulse.detuning, pulse.rabi.amplitude, pulse.rabi.phase}),
        level_couplings=frozenset({sequence.hyperfine, sequence.rydberg}),
    )
