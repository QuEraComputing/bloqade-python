from bloqade import start
import numpy as np

plateau_time = (np.pi / 2 - 0.625) / 12.5
wf_durations = [0.05, plateau_time, 0.05, "t_run", 0.05, plateau_time, 0.05]
rabi_wf_values = [0.0, 12.5, 12.5, 0.0] * 2  # repeat values twice


ramsey_program = (
    start.add_position([0, 0])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(wf_durations, rabi_wf_values)
    .detuning.uniform.piecewise_linear(wf_durations, [10.5] * (len(wf_durations) + 1))
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
