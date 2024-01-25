from bloqade.atom_arrangement import Chain
import numpy as np


def test_z2_compile():
    # Define relevant parameters for the lattice geometry and pulse schedule
    n_atoms = 11
    lattice_spacing = 6.1
    min_time_step = 0.05

    # Define Rabi amplitude and detuning values.
    # Note the addition of a "sweep_time" variable
    # for performing sweeps of time values.
    rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
    rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
    durations = [0.8, "sweep_time", 0.8]

    time_sweep_z2_prog = (
        Chain(n_atoms, lattice_spacing=lattice_spacing)
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations, rabi_amplitude_values
        )
        .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
    )

    # Allow "sweep_time" to assume values from 0.05 to 2.4 microseconds for a total of
    # 20 possible values.
    # Starting at exactly 0.0 isn't feasible so we use the `min_time_step` defined
    # previously.
    time_sweep_z2_job = time_sweep_z2_prog.batch_assign(
        sweep_time=np.linspace(min_time_step, 2.4, 20)
    )

    bloqade_emu_target = time_sweep_z2_job.bloqade.python()
    braket_emu_target = time_sweep_z2_job.braket.local_emulator()
    quera_aquila_target = time_sweep_z2_job.parallelize(24).quera.aquila()
    braket_aquila_target = time_sweep_z2_job.parallelize(24).braket.aquila()

    targets = [
        bloqade_emu_target,
        braket_emu_target,
        quera_aquila_target,
        braket_aquila_target,
    ]

    for target in targets:
        target._compile(10)
