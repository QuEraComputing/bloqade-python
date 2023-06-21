# Written by Phillip Weinberg as part of PR #217 introducing
# Slice and Record builders

import numpy as np

from bloqade import var
from bloqade.ir.location import Chain

n_atoms = 11
atom_spacing = 6.1
run_time = var("run_time")

quantum_scar_program = (
    Chain(n_atoms, lattice_spacing=atom_spacing)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        [0.3, 1.6, 0.3], [0.0, 15.7, 15.7, 0.0]
    )
    .piecewise_linear([0.2, 1.4, 0.2], [0, 15.7, 15.7, 0])
    .slice(stop=run_time - 0.06)
    .record("rabi_value")
    .linear("rabi_value", 0, 0.06)
    .detuning.uniform.piecewise_linear([0.3, 1.6, 0.3], [-18.8, -18.8, 16.3, 16.3])
    .piecewise_linear([0.2, 1.6], [16.3, 0.0, 0.0])
    .slice(stop=run_time)
)


# get run times via the following:
prep_times = np.around(np.arange(0.2, 2.2, 0.2), 13)
scar_times = np.around(np.arange(2.2, 4.01, 0.01), 13)
run_times = np.unique(np.hstack((prep_times, scar_times)))

if __name__ == "__main__":
    quantum_scar_job = (
        quantum_scar_program.batch_assign(run_time=run_times)
        .braket_local_simulator(10000)
        .submit(multiprocessing=True)
        .report()
        .rydberg_densities()
    )
    print(quantum_scar_job)
