from bloqade import piecewise_linear, start, var, cast
from bloqade.atom_arrangement import Chain
from bloqade.ir import (
    rydberg,
    detuning,
    AnalogCircuit,
    Sequence,
    Pulse,
    Field,
    AssignedRunTimeVector,
    Uniform,
)
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.compiler.rewrite.common.assign_variables import AssignBloqadeIR
from bloqade.compiler.analysis.common.assignment_scan import AssignmentScan
from decimal import Decimal
import pytest


def test_assignment():
    lattice = Chain(2, lattice_spacing=4.5)
    circuit = (
        lattice.rydberg.detuning.scale("amp")
        .piecewise_linear([0.1, 0.5, 0.1], [1.0, 2.0, 3.0, 4.0])
        .parse_circuit()
    )

    amp = 2 * [Decimal("1.0")]
    circuit = AssignBloqadeIR(dict(amp=amp)).visit(circuit)

    target_circuit = AnalogCircuit(
        lattice,
        Sequence(
            {
                rydberg: Pulse(
                    {
                        detuning: Field(
                            drives={
                                AssignedRunTimeVector("amp", amp): piecewise_linear(
                                    [0.1, 0.5, 0.1], [1.0, 2.0, 3.0, 4.0]
                                )
                            }
                        ),
                    }
                )
            }
        ),
    )

    assert circuit == target_circuit


def test_assignment_error():
    lattice = Chain(2, lattice_spacing=4.5)
    circuit = (
        lattice.rydberg.detuning.scale("amp")
        .piecewise_linear([0.1, 0.5, 0.1], [1.0, 2.0, 3.0, 4.0])
        .parse_circuit()
    )

    amp = 2 * [Decimal("1.0")]
    circuit = AssignBloqadeIR(dict(amp=amp)).visit(circuit)
    with pytest.raises(ValueError):
        circuit = AssignBloqadeIR(dict(amp=amp)).visit(circuit)


def test_scan():
    t = var("t")
    circuit = (
        start.rydberg.detuning.uniform.constant("max", 1.0)
        .slice(0, t)
        .record("detuning")
        .linear("detuning", 0, 1.0 - t)
        .parse_sequence()
    )

    params = dict(max=10, t=0.1)

    completed_params = AssignmentScan(params).emit(circuit)
    completed_circuit = AssignBloqadeIR(completed_params).visit(circuit)

    t_assigned = scalar.AssignedVariable("t", 0.1)
    max_assigned = scalar.AssignedVariable("max", 10)
    detuning_assigned = scalar.AssignedVariable("detuning", 10)
    dur_assigned = 1 - t_assigned

    interval = waveform.Interval(cast(0), t_assigned)

    target_circuit = Sequence(
        {
            rydberg: Pulse(
                {
                    detuning: Field(
                        drives={
                            Uniform: waveform.Append(
                                [
                                    waveform.Slice(
                                        waveform.Constant(max_assigned, cast(1.0)),
                                        interval,
                                    ),
                                    waveform.Linear(detuning_assigned, 0, dur_assigned),
                                ]
                            )
                        }
                    )
                }
            )
        }
    )

    print(repr(completed_circuit))
    print(repr(target_circuit))

    assert completed_circuit == target_circuit
