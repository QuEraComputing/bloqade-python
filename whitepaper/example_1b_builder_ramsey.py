from bloqade import start
import numpy as np

plateau_time = (np.pi / 2 - 0.625) / 12.5
pi_over_two_durations = [0.05, plateau_time, 0.05]
pi_over_two_values = [0.0, 12.5, 12.5, 0.0]


ramsey_program = (
    start.add_position([0, 0])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=pi_over_two_durations, values=pi_over_two_values
    )
    .constant(value=0, duration="t_run")
    .piecewise_linear(durations=pi_over_two_durations, values=pi_over_two_values)
    .detuning.uniform.piecewise_constant(
        durations=pi_over_two_durations + ["t_run"] + pi_over_two_durations,
        values=[10.5] * 7,
    )
)

# run on local emulator
ramsey_job = (
    ramsey_program.batch_assign(t_run=np.around(np.arange(0, 30, 1) * 0.1, 13))
    .braket_local_simulator(10000)
    .submit()
    .report()
    .rydberg_densities()
)

# run on HW
# ramsey_program.parallelize(24).batch_assign(
#    t_run=np.around(np.arange(0, 30, 1) * 0.1, 13)
# ).mock(100)
