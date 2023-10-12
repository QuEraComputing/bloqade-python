# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     hide_notebook_metadata: false
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.5
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Single Qubit Rabi Oscillations
# ## Introduction
# In this example we show how to use Bloqade to emulate a
# Rabi oscillation as well as run it on hardware.

# %%
from bloqade import start, cast
from bloqade.task.json import load_batch, save_batch
from decimal import Decimal
import matplotlib.pyplot as plt


# %% [markdown]

# define program with one atom, with constant detuning but variable Rabi frequency,
# ramping up to "rabi_value" and then returning to 0.0.

# %%
durations = cast(["ramp_time", "run_time", "ramp_time"])

rabi_oscillations_program = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=durations, values=[0, "rabi_value", "rabi_value", 0]
    )
    .detuning.uniform.constant(duration=sum(durations), value=0)
)

# %% [markdown]
# Assign values to the variables in the program,
# allowing the `run_time` (time the Rabi amplitude stays at the value of
# "rabi_frequency" ) to sweep across a range of values.

# %%
rabi_oscillation_job = rabi_oscillations_program.assign(
    ramp_time=0.06, rabi_value=15, detuning_value=0.0
).batch_assign(run_time=[Decimal("0.05") * i for i in range(21)])

# %% [markdown]
# Run the program in emulation, obtaining a report
# object. For each possible set of variable values
# to simulate (in this case, centered around the
# `run_time` variable), let the task have 10000 shots.

# %%
emulator_results = rabi_oscillation_job.braket.local_emulator().run(1000)
save_batch("rabi-emulator-job.json", emulator_results)


# %% [markdown]
# Submit the same program to hardware,
# this time using `.parallelize` to make a copy of the original geometry
# (a single atom) that fills the FOV (Field-of-View Space), with at least
# 24 micrometers of distance between each atom.
#
# Unlike the emulation above, we only let each task
# run with 100 shots. A collection of tasks is known as a
# "Job" in Bloqade and jobs can be saved in JSON format
# so you can reload them later (a necessity considering
# how long it may take for the machine to handle tasks in the queue)

# %%
"""
hardware_result = rabi_oscillation_job.parallelize(24).braket.aquila().submit(1000)
save_batch("rabi-job.json", hardware_result)
"""

# %% [markdown]
# Load JSON and pull results from Braket

# %%
emulator_report = load_batch("rabi-emulator-job.json").report()
# hardware_report = load_batch("rabi-job.json").fetch().report()

times = emulator_report.list_param("run_time")
bitstrings = emulator_report.bitstrings()
emu_density = [ele.mean() for ele in bitstrings]
plt.plot(times, emu_density)

# bitstrings = hardware_report.bitstrings()
# qpu_density = [ele.mean() for ele in bitstrings]

# plt.plot(times, qpu_density)
plt.show()


# %%
