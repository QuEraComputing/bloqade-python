from bloqade import start
import numpy as np


if __name__ == "__main__":
    simulator_job = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "run_time", 0.1], [0, 15, 15, 0]
        )
        .batch_assign(run_time=np.linspace(0.1, 3.8, 20))
        .braket_local_simulator(1000)
    )

    rydberg_densities = simulator_job.submit().report().rydberg_densities()

    rydberg_densities = (
        simulator_job.submit(multiprocessing=True).report().rydberg_densities()
    )
