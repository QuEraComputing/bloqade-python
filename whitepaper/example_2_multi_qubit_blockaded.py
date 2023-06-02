from bloqade import start
from bloqade.ir import Variable, Literal
import numpy as np

# simple rabi drive, goes to 5
# flat detuning and phase at 0.0


# Tried "assigning" start to another variable and then returning 
# that other variable at the end of the if-elif chain but you end up 
# with n_atoms = 0 which causes parallelization to fall flat
def program_init(num_atoms):
    distance = 4
    inv_sqrt_2_rounded = 2.6

     # taking the pointer so that new_program has the same thing

    
    if num_atoms == 1:
        new_program = start.add_position((0,0))
    elif num_atoms == 2:
        new_program = start.add_positions([(0,0), 
                               (0, distance)])
    elif num_atoms == 3:
        new_program = start.add_positions([(-inv_sqrt_2_rounded, 0),
                               (inv_sqrt_2_rounded, 0),
                               (0, distance)])
    elif num_atoms == 4:
        new_program = start.add_positions([(0,0),
                               (distance, 0),
                               (0, distance),
                               (distance, distance)])
    elif num_atoms == 7:
        new_program = start.add_positions([(0,0),
                               (distance, 0),
                               (-0.5*distance, distance),
                               (0.5*distance, distance),
                               (1.5*distance, distance),
                               (0, 2*distance),
                               (distance, 2*distance)])
    else:
        raise ValueError(f"natoms must be 1, 2, 3, 4, or 7")

    print(new_program.n_atoms)
    return new_program

program = program_init(7)

RAMP_TIME = 0.06
durations = [RAMP_TIME, Variable("t_run"), RAMP_TIME]
values = [0, 5, 5, 0]

multi_qubit_blockade_program = (
    program
    .rydberg
    .rabi
    .amplitude
    .uniform
    .piecewise_linear(
        durations = durations, 
        values = values
    )
    .detuning
    .uniform
    .constant(
        value = 0,
        duration = Literal(2 * RAMP_TIME) + Variable("t_run")
    )
)

(
    multi_qubit_blockade_program
    .parallelize(24)
    .batch_assign(t_run = 0.05 * np.arange(21))
    .mock(1000)
)