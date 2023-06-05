from bloqade.ir.scalar import Variable
import numpy as np
from bloqade import start


durations = [Variable("ramp_time"), Variable("run_time"), Variable("ramp_time")]

rabi_oscillations_program = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=durations, values=[0, "rabi_value", "rabi_value", 0]
    )
    .detuning.uniform.piecewise_linear(
        durations=durations, values=[0, "detuning_value", "detuning_value", 0]
    )
)


rabi_oscillations_program.parallelize(24).assign(
    ramp_time=0.06, rabi_value=15, detuning_value=0.0
).batch_assign(run_time=np.around(np.arange(0, 21, 1) * 0.05, 13)).mock(10, "test.txt")
