from bloqade.ir.location import Chain


from bokeh.plotting import figure, show
from bokeh.layouts import row
import numpy as np

n_atoms = 11
lattice_const = 6.1

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
durations = [0.8, "sweep_time", 0.8]

fixed_1d_z2_prog = (
    Chain(n_atoms, lattice_const)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

fixed_1d_z2_job = fixed_1d_z2_prog.assign(sweep_time=2.4)

# Emulator
emu_job = fixed_1d_z2_job.braket_local_simulator(10000).submit().report()

# Hardware
hw_job = (
    fixed_1d_z2_job.parallelize(3 * lattice_const)
    .braket(100)
    .submit()
    .save_json("example-3-fixed-1d-z2-job.json")
)


# get densities
fixed_1d_z2_densities = emu_job.rydberg_densities()

# plot density at end of evolution
end_evolution_densities = figure(
    title="Simulated Densities",
    toolbar_location=None,
    tools="",
)

end_evolution_densities.vbar(
    x=list(range(n_atoms)), top=fixed_1d_z2_densities.iloc[0], width=0.9
)

end_evolution_densities.title.text_font_size = "15pt"
end_evolution_densities.axis.axis_label_text_font_size = "15pt"
end_evolution_densities.axis.major_label_text_font_size = "10pt"

end_evolution_densities.xaxis.ticker = list(range(11))
end_evolution_densities.xaxis.axis_label = "Site Index"
end_evolution_densities.yaxis.axis_label = "Rydberg Density"

end_evolution_densities.y_range.start = 0

# Get states and their associated probabilities

state_counts = emu_job.counts[0]
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

probable_states = figure(
    x_range=top_n_states,
    title="Simulated Probabilities",
    toolbar_location=None,
    tools="",
)

probable_states.vbar(x=top_n_states, top=top_n_probabilities, width=0.9)

probable_states.title.text_font_size = "15pt"
probable_states.axis.axis_label_text_font_size = "15pt"
probable_states.axis.major_label_text_font_size = "10pt"

probable_states.xaxis.major_label_orientation = np.pi / 4
probable_states.xaxis.axis_label = "Measured State"
probable_states.yaxis.axis_label = "Probability"

probable_states.y_range.start = 0

# correlation plot
correlation_table = np.zeros((n_atoms, n_atoms))

# correlation plot doesn't look right here, probably something off in how I'm doing this
for i in range(n_atoms):
    for j in range(n_atoms):
        correlation_table[i, j] = (
            (1 - emu_job.dataframe.iloc[:, i]) * (1 - emu_job.dataframe.iloc[:, j])
        ).mean() - fixed_1d_z2_densities.iloc[0, i] * fixed_1d_z2_densities.iloc[0, j]

correlation_plot = figure(
    title="Simulated Correlation",
    x_range=(0, n_atoms),
    y_range=(0, n_atoms),
    toolbar_location=None,
    tools="",
)

correlation_plot.image(
    image=[correlation_table], palette="Plasma256", x=0, y=0, dw=n_atoms, dh=n_atoms
)

correlation_plot.title.text_font_size = "15pt"
correlation_plot.axis.axis_label_text_font_size = "15pt"
correlation_plot.axis.major_label_text_font_size = "10pt"

correlation_plot.xaxis.axis_label = "index i"
correlation_plot.yaxis.axis_label = "index j"

p = row(end_evolution_densities, probable_states, correlation_plot)

show(p)
