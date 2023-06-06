from bloqade import start
from bloqade.ir import cast
import matplotlib.pyplot as plt
import numpy as np

n_atoms = 11

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
durations = [0.8, "sweep_time", 0.8]

fixed_1d_z2_prog = (
    start.add_positions([(0.0, i * cast("lattice_constant")) for i in range(n_atoms)])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

fixed_1d_z2_job = fixed_1d_z2_prog.assign(
    lattice_constant=6.1, sweep_time=2.4
).braket_local_simulator(10000)

report = fixed_1d_z2_job.submit().report()

# plot density at end of evolution

plt.rcParams["font.size"] = 20
plt.rcParams["font.family"] = ["serif"]

rydberg_densities = report.rydberg_densities()
fixed_1d_z2_results = rydberg_densities.iloc[0]

plt.title("Simulated Densities")
plt.bar(range(n_atoms), fixed_1d_z2_results, color="grey")
plt.xlabel("Site Index")
plt.ylabel("Rydberg Density")

# plot states with highest probabilities at end of evolution

state_counts = report.counts[0]
state_probabilities = {state: counts / 10000 for state, counts in state_counts.items()}
sorted_state_probabilities = sorted(
    state_probabilities.items(), key=lambda item: item[1], reverse=True
)

# top n most probable states
n_probable_states = 7
# want to get the first 7
top_n_states = []
top_n_probabilities = []
for i in range(n_probable_states):
    state, probability = sorted_state_probabilities[i]
    top_n_states.append(state)
    top_n_probabilities.append(probability)

plt.bar(range(n_probable_states), top_n_probabilities, color="grey")
plt.title("Simulated Probabilities")
plt.xlabel("Measured State")
plt.ylabel("Probability")
plt.xticks(range(n_probable_states), top_n_states, rotation=90)
plt.tick_params(axis="x", direction="in", pad=-175)

# correlation plot
correlation_table = np.zeros((n_atoms, n_atoms))

# correlation plot doesn't look right here, probably something off in how I'm doing this
for i in range(n_atoms):
    for j in range(n_atoms):
        correlation_table[i, j] = (
            (1 - report.dataframe.iloc[:, i]) * (1 - report.dataframe.iloc[:, j])
        ).mean() - rydberg_densities.iloc[0, i] * rydberg_densities.iloc[0, j]


plt.matshow(correlation_table, cmap="plasma")
plt.title("Simulated Correlation")
plt.xlabel("index i")
plt.ylabel("index j")
