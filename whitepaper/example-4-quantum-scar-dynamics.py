import numpy as np

from bloqade import start
from bloqade.ir import Linear, Constant

n_atoms = 11
atom_spacing = 6.1 

rabi_adiabatic_prep = (
    Linear(start = 0.0, stop = 15.7, duration = 0.3)
    .append(
        Constant(value = 15.7, duration = 1.6)
    )
    .append(
        Linear(start = 15.7, stop = 0.0, duration = 0.3)
    )
)

rabi_scar_dynamics = (
    Linear(start = 0.0, stop = 15.7, duration = 0.2)
    .append(
        Constant(value = 15.7, duration = 1.8)
    )
    .append(
        Linear(start = 15.7, stop = 0.0, duration = 0.2)
    )
)

rabi_wf = rabi_adiabatic_prep.append(rabi_scar_dynamics)
 
detuning_adiabatic_prep = (
    Constant(value = -18.8, duration = 0.3)
    .append(
        Linear(start = -18.8, stop = 16.3, duration=1.6)
    )
    .append(
        Constant(value = 16.3, duration=0.3)
    )
)

detuning_scar_dynamics = (
    Linear(start = 16.3, stop = 0.0, duration = 0.2)
    .append(
        Constant(value = 0.0, duration = 1.8 + 0.2)
    )
)

detuning_wf = detuning_adiabatic_prep.append(detuning_scar_dynamics)

quantum_scar_program = (
    start
    .add_positions(
        [(0.0, atom_spacing*i) for i in range(11)]
    )
    .rydberg
    .rabi
    .amplitude
    .uniform
    .apply(rabi_wf[:"run_time"])
    .detuning
    .uniform
    .apply(detuning_wf[:"run_time"])
    # phase is always zero, can omit safely here
)

# get run times via the following:
prep_times = np.around(np.arange(0.2,2.2,0.2),13) 
scar_times = np.around(np.arange(2.2,4.01,0.01),13)
run_times = np.unique(np.hstack((prep_times, scar_times)))

quantum_scar_job = (
    quantum_scar_program
    .batch_assign(run_time = run_times)
    .braket_local_simulator(10000)
)

