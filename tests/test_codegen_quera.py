from bloqade.ir import (
    rydberg,
    detuning,
    Sequence,
    Field,
    Pulse,
    Uniform,
    Linear,
    Interval,
)
from bloqade import cast
import bloqade.codegen.common.assignment_scan as asn
from bloqade.ir.control.sequence import NamedSequence
from bloqade.ir.control.pulse import Slice


def test_assignment_scan_app():
    f = Field({Uniform: Linear(start=1.0, stop=2.0, duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    app = seq_full.append(seq_full)

    asgn = {"test": 40}
    scanner = asn.AssignmentScan({"test": 40})

    assert scanner.emit(app) == asgn


def test_assignment_scan_slice():
    f = Field({Uniform: Linear(start=1.0, stop=2.0, duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    seq = seq_full[:1.0]

    asgn = {"test": 40}
    scanner = asn.AssignmentScan({"test": 40})

    assert scanner.emit(seq) == asgn


def test_assignment_scan_namedseq():
    f = Field({Uniform: Linear(start=1.0, stop=2.0, duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    seq = NamedSequence(seq_full, "qq")

    asgn = {"test": 40}
    scanner = asn.AssignmentScan({"test": 40})

    assert scanner.emit(seq) == asgn


def test_assignment_scan_waveform():
    wv = Linear(start=1.0, stop=2.0, duration=3.0)
    wf = wv + wv

    f = Field({Uniform: wf})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    asgn = {"test": 40}
    scanner = asn.AssignmentScan(asgn)

    assert scanner.emit(seq_full) == asgn


def test_assignment_scan_pulse_app():
    wv = Linear(start=1.0, stop=2.0, duration=3.0)

    f = Field({Uniform: wv})
    ps = Pulse({detuning: f})
    pss = ps.append(ps)
    seq_full = Sequence({rydberg: pss})

    asgn = {"test": 40}
    scanner = asn.AssignmentScan(asgn)

    assert scanner.emit(seq_full) == asgn


def test_assignment_scan_pulse_slice():
    wv = Linear(start=1.0, stop=2.0, duration=3.0)

    f = Field({Uniform: wv})
    ps = Pulse({detuning: f})
    pss = Slice(pulse=ps, interval=Interval(None, cast(1.0)))
    seq_full = Sequence({rydberg: pss})

    asgn = {"test": 40}
    scanner = asn.AssignmentScan(asgn)

    assert scanner.emit(seq_full) == asgn
