from bloqade import start, cast
import numpy as np


def program_init(num_atoms):
    distance = 4
    inv_sqrt_2_rounded = 2.6

    if num_atoms == 1:
        new_program = start.add_position((0, 0))
    elif num_atoms == 2:
        new_program = start.add_positions([(0, 0), (0, distance)])
    elif num_atoms == 3:
        new_program = start.add_positions(
            [(-inv_sqrt_2_rounded, 0), (inv_sqrt_2_rounded, 0), (0, distance)]
        )
    elif num_atoms == 4:
        new_program = start.add_positions(
            [(0, 0), (distance, 0), (0, distance), (distance, distance)]
        )
    elif num_atoms == 7:
        new_program = start.add_positions(
            [
                (0, 0),
                (distance, 0),
                (-0.5 * distance, distance),
                (0.5 * distance, distance),
                (1.5 * distance, distance),
                (0, 2 * distance),
                (distance, 2 * distance),
            ]
        )
    else:
        raise ValueError("natoms must be 1, 2, 3, 4, or 7")

    return new_program


program = program_init(7)

durations = cast(["ramp_time", "t_run", "ramp_time"])

multi_qubit_blockade_program = program.rydberg.rabi.amplitude.uniform.piecewise_linear(
    durations, [0, 5, 5, 0]
).detuning.uniform.constant(value=0, duration=sum(durations))

# run on local emulator

multi_qubit_blockade_job = (
    multi_qubit_blockade_program.batch_assign(t_run=0.05 * np.arange(21))
    .assign(ramp_time=0.06)
    .braket_local_simulator(10000)
    .submit()
    .report()
    .rydberg_densities()
)

# run on hardware
"""
(
    multi_qubit_blockade_program.parallelize(24)
    .assign(ramp_time=0.06)
    .batch_assign(t_run=0.05 * np.arange(21))
    .mock(1000)
)
"""
