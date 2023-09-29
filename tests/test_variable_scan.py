from bloqade import start, var
from bloqade.atom_arrangement import Chain
from bloqade.ir.analysis.scan_variables import (
    ScanVariablesAnalogCircuit,
    ScanVariableResults,
)
import numpy as np

from bloqade.ir.control.waveform import instruction


def test_1():
    def detuning_wf(t, delta, omega=15):
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


def test_2():
    t = var("t")

    t_2 = var("T").max(t)
    t_1 = var("T").min(t)

    delta = var("delta") / (2 * np.pi)
    omega_max = var("omega_max") * 2 * np.pi

    @instruction(t_2)
    def detuning(t, u):
        return np.abs(t) * u

    circuit = (
        start.add_position(("x", "y"))
        .add_position(("a", "b"))
        .rydberg.rabi.amplitude.var("mask")
        .piecewise_linear([0.1, t - 0.2, 0.1], [0, omega_max, omega_max, 0])
        .slice(t_1, t_2)
        .uniform.poly([1, 2, 3, 4], t_1)
        .detuning.uniform.constant(10, t_2)
        .uniform.linear(0, delta, t_1)
        .phase.uniform.apply(-(2 * detuning))
        .parallelize(20.0)
        .parse_circuit()
    )

    scalar_vars = ["t", "x", "y", "delta", "T", "omega_max", "a", "u", "b"]
    vector_vars = ["mask"]
    expected_result = ScanVariableResults(
        scalar_vars=scalar_vars, vector_vars=vector_vars
    )
    assert expected_result == ScanVariablesAnalogCircuit().emit(circuit)
