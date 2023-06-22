from bloqade import start
import numpy as np

delta = 0.377371  # Detuning
xi = 3.90242  # Phase jump
tau = 4.29268  # Time of each pulse

amplitude_max = 10
min_time_step = 0.05
detuning_value = delta * amplitude_max
T = (
    tau / amplitude_max - min_time_step
)  # this T ends up being smaller than the minimum time step

durations = [
    min_time_step,
    T,
    min_time_step,
    min_time_step,
    min_time_step,
    T,
    min_time_step,
]
rabi_wf_values = [
    0.0,
    amplitude_max,
    amplitude_max,
    0.0,
    0.0,
    amplitude_max,
    amplitude_max,
    0.0,
]

lp_gate_program = (
    start.add_position((0, 0))
    .add_position((0, 4))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_wf_values)
    .slice(0, "t_run")
    .detuning.uniform.piecewise_linear(
        durations, [detuning_value] * (len(durations) + 1)
    )
    .slice(0, "t_run")
    .phase.uniform.piecewise_constant(durations, [0.0] * 4 + [xi] * 3)
    .slice(0, "t_run")
)

# submit to emulator
lp_gate_job = (
    lp_gate_program.batch_assign(
        t_run=np.arange(min_time_step, sum(durations), min_time_step)
    )  # not happy starting from t_run = 0.0, have to offset a little
    .braket_local_simulator(10000)
    .submit()
    .report()
    .rydberg_densities()
)

# can plot in terminal via plotext
"""
import plotext as plt
plt.plot(lp_gate_job.iloc[:,0])
plt.plot(lp_gate_job.iloc[:,1])
plt.show()
"""
