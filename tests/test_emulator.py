from bloqade import start
import numpy as np


def integration_test():
    (
        start.add_position((0, 0))
        .add_position((0, 1.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, "ramp_time", 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, "ramp_time", 0.1], [0, 10, 10, 0])
        .assign(ramp_time=3.0)
        .batch_assign(r=np.linspace(4, 10, 31).tolist())
        .bloqade.python()
        .run(10000, cache_matrices=True)
        .report()
        .bitstrings()
    )
