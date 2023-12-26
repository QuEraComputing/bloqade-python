from bloqade.atom_arrangement import Chain
from bloqade.compiler.analysis.common.is_constant import IsConstant


def test_happy_path():
    circuit = (
        Chain(8, lattice_spacing=6.1)
        .rydberg.detuning.uniform.constant(1.0, 10.0)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .phase.uniform.poly([1.0, 0.0, 0.0, 0.0, 0.0], 10)
        .parse_circuit()
    )

    assert IsConstant().scan(circuit)

    circuit = (
        Chain(8, lattice_spacing=6.1)
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
    assert IsConstant().scan(circuit)


def test_fail_shape():
    circuit = (
        Chain(8, lattice_spacing=6.1)
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
    assert not IsConstant().scan(circuit)

    circuit = (
        Chain(8, lattice_spacing=6.1)
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
    assert not IsConstant().scan(circuit)


def test_fail_duration():
    circuit = (
        Chain(8, lattice_spacing=6.1)
        .rydberg.detuning.uniform.constant(1.0, 9.0)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .phase.uniform.poly([1.0, 0.0, 0.0, 0.0, 0.0], 10)
        .parse_circuit()
    )

    print(circuit)
    # assert False
    assert not IsConstant().scan(circuit)

    circuit = (
        Chain(8, lattice_spacing=6.1)
        .rydberg.detuning.uniform.constant(1.0, 10.0)
        .uniform.constant(1.0, 9.0)
        .amplitude.uniform.linear(1.0, 1.0, 5.0)
        .linear(1.0, 1.0, 5.0)
        .phase.uniform.poly([1.0, 0.0, 0.0, 0.0, 0.0], 10)
        .parse_circuit()
    )

    print(circuit)
    # assert False
    assert not IsConstant().scan(circuit)


def test_fail_value():
    circuit = (
        Chain(8, lattice_spacing=6.1)
        .rydberg.detuning.uniform.constant(1.0, 10.0)
        .constant(1.1, 10.0)
        .parse_circuit()
    )

    print(circuit)
    # assert False
    assert not IsConstant().scan(circuit)
