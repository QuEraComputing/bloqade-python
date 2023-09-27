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
