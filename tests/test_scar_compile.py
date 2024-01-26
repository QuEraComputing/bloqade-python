from bloqade import var
from bloqade.atom_arrangement import Chain
import numpy as np


def test_scar_compile():
    n_atoms = 11
    lattice_spacing = 6.1
    run_time = var("run_time")

    quantum_scar_program = (
        Chain(n_atoms, lattice_spacing=lattice_spacing)
        # define detuning waveform
        .rydberg.detuning.uniform.piecewise_linear(
            [0.3, 1.6, 0.3], [-18.8, -18.8, 16.3, 16.3]
        )
        .piecewise_linear([0.2, 1.6], [16.3, 0.0, 0.0])
        # slice the detuning waveform
        .slice(start=0, stop=run_time)
        # define rabi waveform
        .amplitude.uniform.piecewise_linear([0.3, 1.6, 0.3], [0.0, 15.7, 15.7, 0.0])
        .piecewise_linear([0.2, 1.4, 0.2], [0, 15.7, 15.7, 0])
        # slice waveform, add padding for the linear segment
        .slice(start=0, stop=run_time - 0.065)
        # record the value of the waveform at the end of the slice to "rabi_value"
        .record("rabi_value")
        # append segment to waveform that fixes the value of the waveform to 0
        # at the end of the waveform
        .linear("rabi_value", 0, 0.065)
    )

    # get run times via the following:
    prep_times = np.arange(0.2, 2.2, 0.2)
    scar_times = np.arange(2.2, 4.01, 0.01)
    run_times = np.unique(np.hstack((prep_times, scar_times)))

    batch = quantum_scar_program.batch_assign(run_time=run_times)

    bloqade_emu_target = batch.bloqade.python()
    braket_emu_target = batch.braket.local_emulator()
    quera_aquila_target = batch.parallelize(24).quera.aquila()
    braket_aquila_target = batch.parallelize(24).braket.aquila()

    targets = [
        bloqade_emu_target,
        braket_emu_target,
        quera_aquila_target,
        braket_aquila_target,
    ]

    for target in targets:
        target._compile(10)
