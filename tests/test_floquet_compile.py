from bloqade import start, cast
import numpy as np


def test_floquet_compile():
    durations = cast(["ramp_time", "run_time", "ramp_time"])

    def detuning_wf(t, drive_amplitude, drive_frequency):
        return drive_amplitude * np.sin(drive_frequency * t)

    floquet_program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations, [0, "rabi_max", "rabi_max", 0]
        )
        .detuning.uniform.fn(detuning_wf, sum(durations))
        .sample("min_time_step", "linear")
    )

    run_times = np.linspace(0.05, 3.0, 101)

    floquet_job = floquet_program.assign(
        ramp_time=0.06,
        min_time_step=0.05,
        rabi_max=15,
        drive_amplitude=15,
        drive_frequency=15,
    ).batch_assign(run_time=run_times)

    bloqade_emu_target = floquet_job.bloqade.python()
    braket_emu_target = floquet_job.braket.local_emulator()
    quera_aquila_target = floquet_job.parallelize(24).quera.aquila()
    braket_aquila_target = floquet_job.parallelize(24).braket.aquila()

    targets = [
        bloqade_emu_target,
        braket_emu_target,
        quera_aquila_target,
        braket_aquila_target,
    ]

    for target in targets:
        target._compile(10)
