from bloqade import start, cast
import numpy as np

drive_frequency = 15
drive_amplitude = 15

durations = cast(["ramp_time", "t_run", "ramp_time"])


def detuning_wf(t):
    return drive_amplitude * np.sin(drive_frequency * t)


floquet_program = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations, [0, "rabi_max", "rabi_max", 0]
    )
    .detuning.uniform.fn(detuning_wf, sum(durations))
    .sample("min_time_step", "linear")  # should sample via minimum time step
)

# submit to hardware
"""
(
    floquet_program
    .parallelize(24)
    .assign(ramp_time = 0.06, min_time_step = 0.05, rabi_max = 15)
    .batch_assign(t_run = np.around(np.linspace(0, 3, 101), 13))
    .mock(1000)
)
"""

# submit to emulator
floquet_job = (
    floquet_program.assign(ramp_time=0.06, min_time_step=0.05, rabi_max=15)
    .batch_assign(t_run=np.around(np.linspace(0, 3, 101), 13))
    .braket_local_simulator(10000)
    .submit()
    .report()
    .rydberg_densities()
)

print(floquet_job)
