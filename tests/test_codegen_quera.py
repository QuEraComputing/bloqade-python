from bloqade.ir import (
    rydberg,
    detuning,
    Sequence,
    Field,
    Pulse,
    Uniform,
    Linear,
    Constant,
    Interval,
    NamedPulse,
)
from bloqade import cast
import bloqade.codegen.common.assignment_scan as asn
import bloqade.codegen.hardware.quera as quer
from bloqade.ir.control.sequence import NamedSequence
from bloqade.ir.control.pulse import Slice


def cf(inlist):
    return list(map(lambda x: float(x), inlist))


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
    ps = ps = NamedPulse("qq", Pulse({detuning: f}))

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


def test_plin_codegen_slice():
    wv = Linear(start=0, stop=1.0, duration=1.0)
    wv = wv.append(Linear(start=1.0, stop=2.0, duration=2.0))

    asgn = {"test": 40}
    scanner = quer.PiecewiseLinearCodeGen(asgn)

    wf = wv[:0.5]
    times, values = scanner.visit_slice(wf)
    assert (cf(times), cf(values)) == ([0, 0.5], [0, 0.5])

    wf2 = wv[0:1]
    times, values = scanner.visit_slice(wf2)
    assert (cf(times), cf(values)) == ([0, 1], [0, 1])

    wf3 = wv[0.7:1]
    times, values = scanner.visit_slice(wf3)
    assert (cf(times), cf(values)) == ([0, 0.3], [0.7, 1])

    wf4 = wv[0:0.6]
    times, values = scanner.visit_slice(wf4)
    assert (cf(times), cf(values)) == ([0, 0.6], [0.0, 0.6])

    wf5 = wv[0.2:0.6]
    times, values = scanner.visit_slice(wf5)
    assert (cf(times), cf(values)) == ([0, 0.4], [0.2, 0.6])

    wf6 = wv[0.6:1.5]
    times, values = scanner.visit_slice(wf6)
    assert (cf(times), cf(values)) == ([0, 0.4, 0.9], [0.6, 1.0, 1.25])

    wf7 = wv[1.0:1.5]
    times, values = scanner.visit_slice(wf7)
    assert (cf(times), cf(values)) == ([0, 0.5], [1.0, 1.25])

    wf8 = wv[1.0:3.0]
    times, values = scanner.visit_slice(wf8)
    assert (cf(times), cf(values)) == ([0, 2.0], [1.0, 2.0])

    wf9 = wv[1.5:3.0]
    times, values = scanner.visit_slice(wf9)
    assert (cf(times), cf(values)) == ([0, 1.5], [1.25, 2.0])


def test_pconst_codegen_slice():
    wv = Constant(value=1.0, duration=1.0)
    wv = wv.append(Constant(value=2.0, duration=1.5))

    asgn = {"test": 40}
    scanner = quer.PiecewiseConstantCodeGen(asgn)

    wf = wv[:1.3]
    times, values = scanner.visit_slice(wf)
    assert (cf(times), cf(values)) == ([0, 1.0, 1.3], [1.0, 2.0, 2.0])

    wf2 = wv[0:1]
    times, values = scanner.visit_slice(wf2)
    assert (cf(times), cf(values)) == ([0, 1.0], [1.0, 1.0])

    wf3 = wv[0.7:1.2]
    times, values = scanner.visit_slice(wf3)
    assert (cf(times), cf(values)) == ([0, 0.3, 0.5], [1.0, 2.0, 2.0])

    wf4 = wv[0.7:1]
    times, values = scanner.visit_slice(wf4)
    assert (cf(times), cf(values)) == ([0, 0.3], [1.0, 1])

    wf4 = wv[0:0.6]
    times, values = scanner.visit_slice(wf4)
    assert (cf(times), cf(values)) == ([0, 0.6], [1.0, 1.0])

    wf5 = wv[0.2:0.6]
    times, values = scanner.visit_slice(wf5)
    assert (cf(times), cf(values)) == ([0, 0.4], [1.0, 1.0])

    wf6 = wv[0:0]
    times, values = scanner.visit_slice(wf6)
    assert (cf(times), cf(values)) == ([0, 0], [0, 0])

    wf8 = wv[1:1]
    times, values = scanner.visit_slice(wf8)
    assert (cf(times), cf(values)) == ([0, 0], [0, 0])

    wf7 = wv[1.3:1.3]
    times, values = scanner.visit_slice(wf7)
    assert (cf(times), cf(values)) == ([0, 0], [0, 0])

    wf9 = wv[1:2.5]
    times, values = scanner.visit_slice(wf9)
    assert (cf(times), cf(values)) == ([0, 1.5], [2.0, 2.0])

    wf10 = wv[1.5:2.5]
    times, values = scanner.visit_slice(wf10)
    assert (cf(times), cf(values)) == ([0, 1.0], [2.0, 2.0])

    wf11 = wv[1:1.5]
    times, values = scanner.visit_slice(wf11)
    assert (cf(times), cf(values)) == ([0, 0.5], [2.0, 2.0])
