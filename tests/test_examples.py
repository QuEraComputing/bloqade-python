from bloqade import start, cast
import numpy as np


def test_example_2():
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
    params = dict(
        drive_amplitude=15,
        drive_frequency=15,
        rabi_max=15,
        ramp_time=0.1,
        run_time=0.1,
        min_time_step=0.05,
    )
    floquet_program.assign(**params).parallelize(20).braket.aquila()._compile(100)
