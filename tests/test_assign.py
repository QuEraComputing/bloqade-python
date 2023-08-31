from bloqade import piecewise_linear
from bloqade.atom_arrangement import Chain
from bloqade.ir import (
    rydberg,
    detuning,
    AnalogCircuit,
    Sequence,
    Pulse,
    Field,
    AssignedRunTimeVector,
)
from bloqade.codegen.common.assign_variables import AssignProgram
from decimal import Decimal


def test_assignment():
    lattice = Chain(2, 4.5)
    circuit = (
        lattice.rydberg.detuning.var("amp")
        .piecewise_linear([0.1, 0.5, 0.1], [1.0, 2.0, 3.0, 4.0])
        .parse_circuit()
    )

    amp = 2 * [Decimal("1.0")]
    circuit = AssignProgram(dict(amp=amp)).visit(circuit)

    target_circuit = AnalogCircuit(
        lattice,
        Sequence(
            {
                rydberg: Pulse(
                    {
                        detuning: Field(
                            value={
                                AssignedRunTimeVector("amp", amp): piecewise_linear(
                                    [0.1, 0.5, 0.1], [1.0, 2.0, 3.0, 4.0]
                                )
                            }
                        )
                    }
                )
            }
        ),
    )

    assert circuit == target_circuit
