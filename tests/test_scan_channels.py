import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence
from bloqade import var

# from bloqade.ir.scalar import var

from bloqade.analysis.common.scan_channels import ScanChannels


def generate_waveforms():
    wf1 = waveform.Constant("v1", "t1")
    wf2 = waveform.Constant("v2", "t2")
    wf3 = waveform.Constant("v3", "t3")
    wf4 = waveform.Constant(4.0, "t4")

    return wf1, wf2, wf3, wf4


def generate_spatiamodulations():
    sm1 = field.UniformModulation()
    sm2 = field.RunTimeVector("mask1")
    sm3 = field.AssignedRunTimeVector("mask2", list(range(4)))
    sm4 = field.ScaledLocations({field.Location(0): "m0", field.Location(2): "m2"})

    return sm1, sm2, sm3, sm4


def generate_fields():
    wf1, wf2, wf3, wf4 = generate_waveforms()
    sm1, sm2, sm3, sm4 = generate_spatiamodulations()

    f1 = field.Field({sm1: wf1})
    f2 = field.Field({sm3: wf3})
    f3 = field.Field({sm2: wf2, sm3: wf3})
    f4 = field.Field({sm2: wf2, sm4: wf4, sm1: wf1})

    return f1, f2, f3, f4


def test_scan_channels_fields():
    sm1, sm2, sm3, sm4 = generate_spatiamodulations()
    f1, f2, f3, f4 = generate_fields()

    assert ScanChannels().scan(f1) == {sm1}
    assert ScanChannels().scan(f2) == {sm3}
    assert ScanChannels().scan(f3) == {sm2, sm3}
    assert ScanChannels().scan(f4) == {sm1, sm2, sm4}


def generate_pulses():
    f1, f2, f3, f4 = generate_fields()

    p1 = pulse.Pulse({pulse.rabi.amplitude: f1})
    p2 = pulse.Pulse({pulse.rabi.phase: f2})
    p3 = pulse.Pulse({pulse.rabi.amplitude: f4, pulse.detuning: f3})

    p4 = p1.append(p2)
    p5 = p3[: var("t")]
    p6 = p4.append(p3)

    return p1, p2, p3, p4, p5, p6


def test_scan_channels_pulses():
    sm1, sm2, sm3, sm4 = generate_spatiamodulations()
    p1, p2, p3, p4, p5, p6 = generate_pulses()

    assert ScanChannels().scan(p1) == {pulse.rabi.amplitude: {sm1}}
    assert ScanChannels().scan(p3) == {
        pulse.rabi.amplitude: {sm1, sm2, sm4},
        pulse.detuning: {sm2, sm3},
    }
    assert ScanChannels().scan(p4) == {
        pulse.rabi.amplitude: {sm1},
        pulse.rabi.phase: {sm3},
    }
    assert ScanChannels().scan(p5) == {
        pulse.rabi.amplitude: {sm1, sm2, sm4},
        pulse.detuning: {sm2, sm3},
    }
    assert ScanChannels().scan(p6) == {
        pulse.rabi.amplitude: {sm1, sm2, sm4},
        pulse.rabi.phase: {sm3},
        pulse.detuning: {sm2, sm3},
    }


def generate_sequences():
    p1, p2, p3, p4, p5, p6 = generate_pulses()

    s1 = sequence.Sequence({sequence.hyperfine: p1})
    s2 = sequence.Sequence({sequence.rydberg: p2})
    s3 = s1.append(s2)
    s4 = s3[: var("t")]

    return s1, s2, s3, s4


def test_scan_channel_sequence():
    sm1, sm2, sm3, sm4 = generate_spatiamodulations()
    s1, s2, s3, s4 = generate_sequences()

    assert ScanChannels().scan(s1) == {
        sequence.hyperfine: {
            pulse.rabi.amplitude: {sm1},
        }
    }
    assert ScanChannels().scan(s2) == {
        sequence.rydberg: {
            pulse.rabi.phase: {sm3},
        }
    }
    assert ScanChannels().scan(s3) == {
        sequence.hyperfine: {
            pulse.rabi.amplitude: {sm1},
        },
        sequence.rydberg: {
            pulse.rabi.phase: {sm3},
        },
    }
    assert ScanChannels().scan(s4) == {
        sequence.hyperfine: {
            pulse.rabi.amplitude: {sm1},
        },
        sequence.rydberg: {
            pulse.rabi.phase: {sm3},
        },
    }
