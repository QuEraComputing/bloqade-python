from bloqade import start
import numpy as np

durations = [1, 2, 1]

two_qubit_adiabatic_program = (
    start.add_positions([(0, 0), (0, "distance")])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, [0, 15, 15, 0])
    .detuning.uniform.piecewise_linear(durations, [-15, -15, 15, 15])
)

# Submit to actual hardware
(
    two_qubit_adiabatic_program.parallelize(24)
    .batch_assign(distance=np.around(np.arange(4, 11, 1), 13))
    .mock(1000)
)
