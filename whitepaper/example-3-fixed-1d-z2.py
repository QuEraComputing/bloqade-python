from bloqade.ir.location import Chain
from bokeh.plotting import figure, show
import numpy as np

n_atoms = 11

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
durations = [0.8, "sweep_time", 0.8]

fixed_1d_z2_prog = (
    Chain(n_atoms, 6.1)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

fixed_1d_z2_report = (
    fixed_1d_z2_prog.assign(sweep_time=2.4)
    .braket_local_simulator(10000)
    .submit()
    .report()
)

# get densities
fixed_1d_z2_densities = fixed_1d_z2_report.rydberg_densities()

# plot density at end of evolution
p = figure(
    title="Simulated Densities",
    toolbar_location=None,
    tools="",
)

p.vbar(x=list(range(n_atoms)), top=fixed_1d_z2_densities.iloc[0], width=0.9)

p.title.text_font_size = "15pt"
p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

p.xaxis.ticker = list(range(11))
p.xaxis.axis_label = "Site Index"
p.yaxis.axis_label = "Rydberg Density"

p.y_range.start = 0

show(p)

# Get states and their associated probabilities

state_counts = fixed_1d_z2_report.counts[0]
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

p = figure(
    x_range=top_n_states,
    title="Simulated Probabilities",
    toolbar_location=None,
    tools="",
)

p.vbar(x=top_n_states, top=top_n_probabilities, width=0.9)

p.title.text_font_size = "15pt"
p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

p.xaxis.major_label_orientation = np.pi / 4
p.xaxis.axis_label = "Measured State"
p.yaxis.axis_label = "Probability"

show(p)

# correlation plot
correlation_table = np.zeros((n_atoms, n_atoms))

# correlation plot doesn't look right here, probably something off in how I'm doing this
for i in range(n_atoms):
    for j in range(n_atoms):
        correlation_table[i, j] = (
            (1 - fixed_1d_z2_report.dataframe.iloc[:, i])
            * (1 - fixed_1d_z2_report.dataframe.iloc[:, j])
        ).mean() - fixed_1d_z2_densities.iloc[0, i] * fixed_1d_z2_densities.iloc[0, j]

p = figure(
    title="Simulated Correlation",
    x_range=(0, n_atoms),
    y_range=(0, n_atoms),
    toolbar_location=None,
    tools="",
)

p.image(
    image=[correlation_table], palette="Plasma256", x=0, y=0, dw=n_atoms, dh=n_atoms
)

p.title.text_font_size = "15pt"
p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

p.xaxis.axis_label = "index i"
p.yaxis.axis_label = "index j"

show(p)
