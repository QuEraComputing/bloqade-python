from bloqade.ir.scalar import Variable
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
    .detuning.uniform.constant(
        value=10.5,
        duration=Variable("t_run") + (2 * np.sum(pi_over_two_durations)),
    )
)

# list object is not calllable
ramsey_program.parallelize(24).batch_assign(
    t_run=np.around(np.arange(0, 30, 1) * 0.1, 13)
).mock(100)
