from bloqade.ir.location import Square

from bokeh.plotting import figure, show
import numpy as np

n_atoms = 11
lattice_const = 5.9

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, "delta_end", "delta_end"]
durations = [0.8, "sweep_time", 0.8]

ordered_state_2D_prog = (
    Square(n_atoms, lattice_const)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

ordered_state_2D_job = ordered_state_2D_prog.assign(delta_end=42.66, sweep_time=2.4)

# Can only run on HW because 121 atoms infeasible on simulator

hw_job = (
    ordered_state_2D_job.braket(100)
    .submit()
    .save_json("example-3-ordered-state-2D-job.json")
)

# Plots
## Density plot
correlation_table = np.zeros((n_atoms, n_atoms))

striated_2d_densities = hw_job.rydberg_densities()

# correlation plot doesn't look right here, probably something off in how I'm doing this
for i in range(n_atoms):
    for j in range(n_atoms):
        correlation_table[i, j] = (
            (1 - hw_job.dataframe.iloc[:, i]) * (1 - hw_job.dataframe.iloc[:, j])
        ).mean() - striated_2d_densities.iloc[0, i] * striated_2d_densities.iloc[0, j]

correlation_plot = figure(
    title="Striated Phase, 5.90 um spacing",
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

p = correlation_plot

show(p)

## G^2
