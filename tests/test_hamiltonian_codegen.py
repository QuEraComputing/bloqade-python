from bloqade.atom_arrangement import Chain
from bloqade.codegen.emulator_ir import EmulatorProgramCodeGen
from bloqade.emulate.codegen.hamiltonian import CompileCache, RydbergHamiltonianCodeGen
from functools import reduce
import numpy as np
import pytest


def get_manybody_op(i, L, op):
    if op.ndim == 1:
        Ident = np.ones_like(op)
    else:
        Ident = np.eye(op.shape[0])

    return reduce(np.kron, [op if j == i else Ident for j in range(L)])


def project_to_subspace(operator, configurations):
    from scipy.sparse import csr_matrix

    proj_shape = (configurations.size, operator.shape[0])
    data = np.ones_like(configurations)
    rows = np.arange(configurations.size)
    cols = configurations
    proj = csr_matrix((data, (rows, cols)), shape=proj_shape)

    if operator.ndim == 1:
        return proj @ operator
    else:
        return proj @ operator @ proj.T


@pytest.mark.parametrize("L", [1, 2, 3, 4, 5, 6])
def test_2_level_uniform(L):
    circuit = (
        Chain(L, lattice_spacing=6.1)
        .rydberg.detuning.uniform.constant(1.0, 1.0)
        .amplitude.uniform.constant(1.0, 1.0)
    ).parse_circuit()

    emu_prog = EmulatorProgramCodeGen().emit(circuit)
    hamiltonian = RydbergHamiltonianCodeGen().emit(emu_prog)
    detuning_op = np.array([0, -1], dtype=int)
    rabi_op = np.array([[0, 1], [1, 0]], dtype=int)

    rabi = sum([get_manybody_op(i, L, rabi_op) for i in range(L)])
    detuning = sum([get_manybody_op(i, L, detuning_op) for i in range(L)])

    assert np.all(hamiltonian.rabi_ops[0].op.tocsr().toarray() == rabi)
    assert np.all(hamiltonian.detuning_ops[0].diagonal == detuning)

    emu_prog = EmulatorProgramCodeGen(blockade_radius=6.2).emit(circuit)
    hamiltonian = RydbergHamiltonianCodeGen().emit(emu_prog)

    rabi_op_proj = project_to_subspace(rabi, hamiltonian.space.configurations)
    detuning_op_proj = project_to_subspace(detuning, hamiltonian.space.configurations)

    assert np.all(hamiltonian.rabi_ops[0].op.tocsr().toarray() == rabi_op_proj)
    assert np.all(hamiltonian.detuning_ops[0].diagonal == detuning_op_proj)


@pytest.mark.parametrize("L", [1, 2, 3, 4])
def test_3_level_uniform(L):
    circuit = (
        Chain(L, lattice_spacing=6.1)
        .hyperfine.detuning.uniform.constant(1.0, 1.0)
        .amplitude.uniform.constant(1.0, 1.0)
    ).parse_circuit()
    cache = CompileCache()
    emu_prog = EmulatorProgramCodeGen().emit(circuit)
    hamiltonian = RydbergHamiltonianCodeGen(cache).emit(emu_prog)

    detuning_op = np.array([0, -1, 0], dtype=int)
    rabi_op = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=int)

    rabi = sum([get_manybody_op(i, L, rabi_op) for i in range(L)])
    detuning = sum([get_manybody_op(i, L, detuning_op) for i in range(L)])

    assert np.all(hamiltonian.rabi_ops[0].op.tocsr().toarray() == rabi)
    assert np.all(hamiltonian.detuning_ops[0].diagonal == detuning)

    emu_prog = EmulatorProgramCodeGen(blockade_radius=6.2).emit(circuit)
    hamiltonian = RydbergHamiltonianCodeGen().emit(emu_prog)

    rabi_op_proj = project_to_subspace(rabi, hamiltonian.space.configurations)
    detuning_op_proj = project_to_subspace(detuning, hamiltonian.space.configurations)

    assert np.all(hamiltonian.rabi_ops[0].op.tocsr().toarray() == rabi_op_proj)
    assert np.all(hamiltonian.detuning_ops[0].diagonal == detuning_op_proj)


@pytest.mark.parametrize(("i", "L"), [(i, L) for L in range(3) for i in range(L)])
def test_2_level_single_atom(i, L):
    circuit = (
        Chain(L, lattice_spacing=6.1)
        .rydberg.detuning.location(i)
        .scale(2.0)
        .constant(1.0, 1.0)
        .amplitude.location(i)
        .scale(0.5)
        .constant(1.0, 1.0)
    ).parse_circuit()
    cache = CompileCache()
    emu_prog = EmulatorProgramCodeGen().emit(circuit)
    hamiltonian = RydbergHamiltonianCodeGen(cache).emit(emu_prog)

    detuning_op = np.array([0, -1], dtype=int)
    rabi_op = np.array([[0, 1], [1, 0]], dtype=int)

    rabi = get_manybody_op(i, L, rabi_op)
    detuning = get_manybody_op(i, L, detuning_op)
    print(rabi)
    print(detuning)
    print(hamiltonian.rabi_ops[0].op.tocsr().toarray())
    assert np.all(hamiltonian.rabi_ops[0].op.tocsr().toarray() == rabi)
    assert np.all(hamiltonian.detuning_ops[0].diagonal == detuning)

    emu_prog = EmulatorProgramCodeGen(blockade_radius=6.2).emit(circuit)
    hamiltonian = RydbergHamiltonianCodeGen().emit(emu_prog)

    rabi_op_proj = project_to_subspace(rabi, hamiltonian.space.configurations)
    detuning_op_proj = project_to_subspace(detuning, hamiltonian.space.configurations)

    assert np.all(hamiltonian.rabi_ops[0].op.tocsr().toarray() == rabi_op_proj)
    assert np.all(hamiltonian.detuning_ops[0].diagonal == detuning_op_proj)
