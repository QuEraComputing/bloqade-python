# from bloqade import start
from bloqade.atom_arrangement import Chain
from bloqade.codegen.common.scan_variables import (
    ScanVariablesAnalogCircuit,
    ScanVariableResults,
)
import numpy as np


def test_1():
    def detuning_wf(t, omega, delta):
        return delta * np.sin(omega * t)

    circuit = (
        Chain(15, "lattice_spacing")
        .rydberg.detuning.var("mask")
        .fn(detuning_wf, "t")
        .amplitude.uniform.constant(15, "t")
        .record("m")
        .phase.location(1)
        .scale("a")
        .piecewise_linear([0.1, 0.5], [0, 1, 1])
        .parse_circuit()
    )

    scalar_vars = ["t", "omega", "delta", "m", "lattice_spacing", "a"]
    vector_vars = ["mask"]
    expected_result = ScanVariableResults(
        scalar_vars=scalar_vars, vector_vars=vector_vars
    )
    assert expected_result == ScanVariablesAnalogCircuit().emit(circuit)
