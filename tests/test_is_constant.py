from bloqade.atom_arrangement import Chain
from bloqade.ir.analysis.is_constant import IsConstantAnalogCircuit


def test_happy_path():
    circuit = (
        Chain(8, 6.1)
        .rydberg.detuning.uniform.constant(1.0, 10.0)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .phase.uniform.poly([1.0, 0.0, 0.0, 0.0, 0.0], 10)
        .parse_circuit()
    )

    result = IsConstantAnalogCircuit().emit(circuit)
    assert result.is_constant

    circuit = (
        Chain(8, 6.1)
        .rydberg.detuning.uniform.constant(1.0, 5.0)
        .uniform.constant(1.0, 10.0)
        .slice(2.5, 7.5)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .slice(2.5, 7.5)
        .record("var")
        .phase.uniform.poly([1.0, 0.0, 0.0, 0.0, 0.0], 5)
        .parse_circuit()
    )
    print(circuit)
    # assert False
    result = IsConstantAnalogCircuit().emit(circuit)
    assert result.is_constant


def test_fail_shape():
    circuit = (
        Chain(8, 6.1)
        .rydberg.detuning.uniform.constant(1.0, 5.0)
        .uniform.constant(1.0, 10.0)
        .slice(2.5, 7.5)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .slice(2.5, 7.5)
        .record("var")
        .phase.uniform.poly([1.0, 1.0, 0.0, 0.0, 0.0], 5)
        .parse_circuit()
    )
    print(circuit)
    # assert False
    result = IsConstantAnalogCircuit().emit(circuit)
    assert not result.is_constant

    circuit = (
        Chain(8, 6.1)
        .rydberg.detuning.uniform.constant(1.0, 5.0)
        .uniform.constant(1.0, 10.0)
        .slice(2.5, 7.5)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .slice(2.5, 7.5)
        .record("var")
        .phase.uniform.poly([1.0, 1.0, 0.0, 0.0, 0.0], 5)
        .amplitude.uniform.fn(lambda t: t, 5)
        .sample(0.05)
        .parse_circuit()
    )
    print(circuit)
    # assert False
    result = IsConstantAnalogCircuit().emit(circuit)
    assert not result.is_constant


def test_fail_duration():
    circuit = (
        Chain(8, 6.1)
        .rydberg.detuning.uniform.constant(1.0, 9.0)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .phase.uniform.poly([1.0, 0.0, 0.0, 0.0, 0.0], 10)
        .parse_circuit()
    )

    print(circuit)
    # assert False
    result = IsConstantAnalogCircuit().emit(circuit)
    assert not result.is_constant

    circuit = (
        Chain(8, 6.1)
        .rydberg.detuning.uniform.constant(1.0, 10.0)
        .uniform.constant(1.0, 9.0)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .phase.uniform.poly([1.0, 0.0, 0.0, 0.0, 0.0], 10)
        .parse_circuit()
    )

    print(circuit)
    # assert False
    result = IsConstantAnalogCircuit().emit(circuit)
    assert not result.is_constant


def test_fail_value():
    circuit = (
        Chain(8, 6.1)
        .rydberg.detuning.uniform.constant(1.0, 10.0)
        .constant(1.1, 10.0)
        .parse_circuit()
    )

    print(circuit)
    # assert False
    result = IsConstantAnalogCircuit().emit(circuit)
    assert not result.is_constant
