from bloqade import start
from bloqade.task import HardwareFuture

import numpy as np
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool, CrosshairTool

plateau_time = (np.pi / 2 - 0.625) / 12.5
wf_durations = [0.05, plateau_time, 0.05, "t_run", 0.05, plateau_time, 0.05]
rabi_wf_values = [0.0, 12.5, 12.5, 0.0] * 2  # repeat values twice


ramsey_program = (
    start.add_position([0, 0])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(wf_durations, rabi_wf_values)
    .detuning.uniform.piecewise_linear(wf_durations, [10.5] * (len(wf_durations) + 1))
)

ramsey_job = ramsey_program.batch_assign(t_run=np.around(np.arange(0, 30, 1) * 0.1, 13))

# run on emulator
emu_job = ramsey_job.braket_local_simulator(10000).submit().report()

# hardware job
"""
(
    ramsey_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("example-1b-ramsey-job.json")
)
"""

# load JSON, get results
hw_future = HardwareFuture()
hw_future.load_json("example-1b-ramsey-job.json")
hw_rydberg_densities = hw_future.report().rydberg_densities()

data = {
    "times": np.around(np.arange(0, 21, 1) * 0.05, 13),
    "emu_densities": emu_job.rydberg_densities()[0].to_list(),
    "hw_densities": hw_rydberg_densities[0].to_list(),
}
source = ColumnDataSource(data=data)

p = figure(
    x_axis_label="Time (μs)",
    y_axis_label="Rydberg Density",
    toolbar_location="right",
    tools=["pan,wheel_zoom,box_zoom,reset,save"],
)

p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

# emulator densities
emu_line = p.line(
    x="times",
    y="emu_densities",
    source=source,
    legend_label="Emulator",
    color="grey",
    line_width=2,
)
p.circle(x="times", y="emu_densities", source=source, color="grey", size=8)
# hardware densities
hw_line = p.line(
    x="times",
    y="hw_densities",
    source=source,
    legend_label="Hardware",
    color="purple",
    line_width=2,
)
p.circle(x="times", y="hw_densities", source=source, color="purple", size=8)

hw_hover_tool = HoverTool(
    renderers=[hw_line],
    tooltips=[
        ("Backend", "Hardware"),
        ("Density", "@hw_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="right",
)
p.add_tools(hw_hover_tool)
emu_hover_tool = HoverTool(
    renderers=[emu_line],
    tooltips=[
        ("Backend", "Emulator"),
        ("Density", "@emu_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="left",
)
p.add_tools(emu_hover_tool)
cross_hair_tool = CrosshairTool(dimensions="height")
p.add_tools(cross_hair_tool)

show(p)
