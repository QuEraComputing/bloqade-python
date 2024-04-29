from bloqade import cast, piecewise_linear
from bloqade.ir.location import Chain

import numpy as np


def test_lattice_gauge_theory_compile():
    N_atom = 13

    detuning_ratio = [0] * N_atom
    detuning_ratio[1 : (N_atom - 1) : 2] = [1, 1, 1, 1, 1, 1]
    detuning_ratio[(N_atom - 1) // 2] = 1

    run_time = cast("run_time")

    rabi_amplitude_wf = piecewise_linear(
        durations=[0.1, 2.0, 0.05, run_time, 0.05],
        values=[0, 5 * np.pi, 5 * np.pi, 4 * np.pi, 4 * np.pi, 0],
    )
    uniform_detuning_wf = piecewise_linear(
        durations=[2.1, 0.05, run_time + 0.05], values=[-6 * np.pi, 8 * np.pi, 0, 0]
    )
    local_detuning_wf = piecewise_linear(
        [0.1, 2.0, 0.05, run_time + 0.05],
        values=[0, -8 * 2 * np.pi, -8 * 2 * np.pi, 0, 0],
    )

    program = (
        Chain(N_atom, lattice_spacing=5.5, vertical_chain=True)
        .rydberg.rabi.amplitude.uniform.apply(rabi_amplitude_wf)
        .detuning.uniform.apply(uniform_detuning_wf)
        .scale(detuning_ratio)
        .apply(local_detuning_wf)
    )

    run_times = np.arange(0.0, 1.05, 0.05)
    batch = program.batch_assign(run_time=run_times)

    bloqade_emu_target = batch.bloqade.python()
    braket_emu_target = batch.braket.local_emulator()
    quera_aquila_target = batch.parallelize(15).quera.aquila()
    braket_aquila_target = batch.parallelize(15).braket.aquila()

    targets = [
        bloqade_emu_target,
        braket_emu_target,
        quera_aquila_target,
        braket_aquila_target,
    ]

    for target in targets:
        target._compile(10)
