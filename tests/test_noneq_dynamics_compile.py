from bloqade.atom_arrangement import Chain
import numpy as np


def test_non_eq_compile():
    initial_geometry = Chain(2, lattice_spacing="distance")
    program_waveforms = (
        initial_geometry.rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=["ramp_time", "run_time", "ramp_time"],
            values=[0.0, "rabi_ampl", "rabi_ampl", 0.0],
        )
    )
    program_assigned_vars = program_waveforms.assign(
        ramp_time=0.06, rabi_ampl=15, distance=8.5
    )
    batch = program_assigned_vars.batch_assign(run_time=0.05 * np.arange(31))

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
