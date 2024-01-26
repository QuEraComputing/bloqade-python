from bloqade import start, cast
from decimal import Decimal
import numpy as np


def test_ramsey_compile():
    plateau_time = (np.pi / 2 - 0.625) / 12.5
    wf_durations = cast(
        [0.05, plateau_time, 0.05, "run_time", 0.05, plateau_time, 0.05]
    )
    rabi_wf_values = [0.0, 12.5, 12.5, 0.0] * 2  # repeat values twice

    ramsey_program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(wf_durations, rabi_wf_values)
        .detuning.uniform.constant(10.5, sum(wf_durations))
    )

    n_steps = 100
    max_time = Decimal("3.0")
    dt = (max_time - Decimal("0.05")) / n_steps
    run_times = [Decimal("0.05") + dt * i for i in range(101)]

    ramsey_job = ramsey_program.batch_assign(run_time=run_times)

    bloqade_emu_target = ramsey_job.bloqade.python()
    braket_emu_target = ramsey_job.braket.local_emulator()
    quera_aquila_target = ramsey_job.parallelize(24).quera.aquila()
    braket_aquila_target = ramsey_job.parallelize(24).braket.aquila()

    targets = [
        bloqade_emu_target,
        braket_emu_target,
        quera_aquila_target,
        braket_aquila_target,
    ]

    for target in targets:
        target._compile(10)
