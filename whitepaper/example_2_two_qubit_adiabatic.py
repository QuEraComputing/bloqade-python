from bloqade import start
import numpy as np
from bloqade.ir import Variable

durations = [1, 2, 1]

two_qubit_adiabatic_program = (
    start.add_positions([(0, 0), (0, Variable("distance"))])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=durations, values=[0, 15, 15, 0]
    )
    .detuning.uniform.piecewise_linear(durations=durations, values=[-15, -15, 15, 15])
)

(
    two_qubit_adiabatic_program.parallelize(24)
    .batch_assign(distance=np.around(np.arange(4, 11, 1), 13))
    .mock(1000)
)
