from bloqade import start
import numpy as np


# Modified from Aquila whitepaper
def generate_random_graph(
    Lx: int, Ly: int, p_filled: float = 0.7, lattice_spacing: float = 5.0, SEED: int = 0
):
    randgen = np.random.RandomState(SEED)

    positions = []
    fillings = []

    for ix in range(Lx):
        for iy in range(Ly):
            filling = True if randgen.uniform() < p_filled else False

            x = np.around(ix * lattice_spacing, 13)
            y = np.around(iy * lattice_spacing, 13)

            positions.append((x, y))
            fillings.append(filling)

    return positions, fillings


# generate positions and fillings, then feed directly into program builder
positions, filling = generate_random_graph(15, 15)

# durations for rabi and detuning
durations = [0.3, 1.6, 0.3]

mis_udg_program = (
    start.add_positions(positions, filling)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, [0.0, 15.0, 15.0, 0.0])
    .detuning.uniform.piecewise_linear(
        durations, [-30, -30, "final_detuning", "final_detuning"]
    )
)

mis_udg_program.batch_assign(final_detuning=np.linspace(0, 80, 81)).mock(1000)
