from bloqade import start, cast
import numpy as np


def test_single_rabi_compile():
    durations = cast(["ramp_time", "run_time", "ramp_time"])

    rabi_oscillations_program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=durations, values=[0, "rabi_ampl", "rabi_ampl", 0]
        )
        .detuning.uniform.constant(duration=sum(durations), value="detuning_value")
    )

    run_times = np.linspace(0, 3, 101)

    rabi_oscillation_job = rabi_oscillations_program.assign(
        ramp_time=0.06, rabi_ampl=15, detuning_value=0.0
    ).batch_assign(run_time=run_times)

    bloqade_emu_target = rabi_oscillation_job.bloqade.python()
    braket_emu_target = rabi_oscillation_job.braket.local_emulator()
    quera_aquila_target = rabi_oscillation_job.parallelize(24).quera.aquila()
    braket_aquila_target = rabi_oscillation_job.parallelize(24).braket.aquila()

    targets = [
        bloqade_emu_target,
        braket_emu_target,
        quera_aquila_target,
        braket_aquila_target,
    ]

    for target in targets:
        target._compile(10)
