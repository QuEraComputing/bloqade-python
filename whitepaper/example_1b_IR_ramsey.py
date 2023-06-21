from bloqade.ir import Linear, Constant
from bloqade import start, var
import numpy as np

plateau_time = (np.pi / 2 - 0.625) / 12.5

# would be nice to have builder functions like what Bloqade has
# (e.g. piecewise_linear, piecewise_constant, etc.)
pi_over_two_pulse = (
    Linear(start=0.0, stop=12.5, duration=0.5)
    .append(Linear(start=12.5, stop=12.5, duration=plateau_time))
    .append(Linear(start=12.5, stop=0.0, duration=0.5))
)
rabi_pulse = pi_over_two_pulse.append(
    Constant(value=0, duration="t_run")
).append(pi_over_two_pulse)


ramsey_program = (
    start.add_position([0, 0])
    .rydberg.rabi.amplitude.uniform.apply(rabi_pulse)
    .detuning.uniform.piecewise_constant(
        durations = [0.5, plateau_time, 0.5, "t_run", 0.5, plateau_time, 0.5],
        values = [10.5] * 7,
    )
)

ramsey_job = (
    ramsey_program
    .batch_assign(t_run=np.around(np.arange(0, 30, 1) * 0.1, 13))
    .braket_local_simulator(10000)
    .submit()
    .report()
    .rydberg_densities()
)

# does not suffer the same problem as using the plain builder syntax for waveform
# run on HW
#ramsey_program.parallelize(24).batch_assign(
#    t_run=np.around(np.arange(0, 30, 1) * 0.1, 13)
#).mock(100)
