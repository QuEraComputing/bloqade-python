from bloqade import start
import numpy as np


rydberg_densities = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        [0.1, "run_time", 0.1], [0, 15, 15, 0]
    )
    .batch_assign(run_time=np.linspace(0.1, 3.8, 20))
    .braket_local_simulator(1000)
    .submit()
    .report()
    .rydberg_densities()
)

print(rydberg_densities)
