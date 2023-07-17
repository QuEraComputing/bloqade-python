# Written by Phillip Weinberg as part of PR #217 introducing
# Slice and Record builders

from bloqade import var
from bloqade.ir.location import Chain
from bloqade.task import HardwareFuture

import numpy as np
from bokeh.plotting import show, figure
from bokeh.layouts import row
from bokeh.models import LinearColorMapper, ColorBar

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
    .slice(stop=run_time - 0.06)
    .record("detuning_value")
    .linear("detuning_value", 0, 0.06)
)

# get run times via the following:
prep_times = np.around(np.arange(0.2, 2.2, 0.2), 13)
scar_times = np.around(np.arange(2.2, 4.01, 0.01), 13)
run_times = np.unique(np.hstack((prep_times, scar_times)))

quantum_scar_job = quantum_scar_program.batch_assign(run_time=run_times)

n_shots = 10000

# run on emulator
emu_job = quantum_scar_job.braket_local_simulator(n_shots).submit().report()

# run on HW
"""
(
    quantum_scar_job.parallelize(24)
    .braket(100)
    .remove_invalid_tasks()
    .submit()
    .save_json("example-4-quantum-scar-dynamics-job.json")
)
"""

# retrieve results from HW
hw_future = HardwareFuture()
hw_future.load_json("example-4-quantum-scar-dynamics-job.json")

# Plot results
## Mean of Rydberg Densities
mean_rydberg_densities_plot = figure(
    title="Mean Rydberg Densities",
    x_axis_label="Run Time (us)",
    y_axis_label="Mean Rydberg Density",
    tools="",
    toolbar_location=None,
)

mean_rydberg_densities_plot.axis.axis_label_text_font_size = "15pt"
mean_rydberg_densities_plot.axis.major_label_text_font_size = "10pt"

mean_rydberg_densities_plot.line(
    run_times, emu_job.rydberg_densities().mean(axis=1), line_width=2
)

## Probability of Ground State

ground_state_probabilities = []
ground_state = "01" * 5 + "0"

for bitstring_counts in emu_job.counts:
    ground_state_probabilities.append(bitstring_counts.get(ground_state, 0) / n_shots)

ground_state_plot = figure(
    title="Probability of Ground State",
    x_axis_label="Run Time (us)",
    y_axis_label="Probability of Ground State",
    tools="",
    toolbar_location=None,
)

ground_state_plot.line(run_times, ground_state_probabilities, line_width=2)

ground_state_plot.axis.axis_label_text_font_size = "15pt"
ground_state_plot.axis.major_label_text_font_size = "10pt"

## Density Plot over Time w/ Interpolation

density_over_time_plot = figure(
    title="Density Over Time",
    x_axis_label="Time (us)",
    y_axis_label="Site",
    tools="",
    toolbar_location=None,
)

density_over_time_plot.axis.axis_label_text_font_size = "15pt"
density_over_time_plot.axis.major_label_text_font_size = "10pt"

density_over_time_plot.x_range.start = 0
density_over_time_plot.y_range.start = 0

densities_array = emu_job.rydberg_densities().to_numpy().transpose()

color_mapping = LinearColorMapper(palette="Viridis11", low=0, high=1)
color_bar = ColorBar(color_mapper=color_mapping)

density_over_time_plot.image(
    image=[emu_job.rydberg_densities().to_numpy().transpose()],
    x=0,
    y=0,
    dw=densities_array.shape[1],
    dh=densities_array.shape[0],
    color_mapper=color_mapping,
)

density_over_time_plot.add_layout(color_bar, "right")

p = row(mean_rydberg_densities_plot, ground_state_plot, density_over_time_plot)

show(p)
