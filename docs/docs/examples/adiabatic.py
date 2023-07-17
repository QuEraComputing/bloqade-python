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
# # Adiabatic Evolution of Rydberg Atoms

# %%
import bloqade.ir.location as location
from bloqade.ir import Linear, Constant

# %% [markdown]
# # split up waveform construction

# %%
detuning_waveform = (
    Constant("initial_detuning", "up_time")
    .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
    .append(Constant("final_detuning", "up_time"))
)

rabi_waveform = (
    Linear(0.0, "rabi_amplitude_max", "up_time")
    .append(Constant("rabi_amplitude_max", "anneal_time"))
    .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
)

task_builder = location.Square(3, lattice_spacing=6.1)
task_builder = task_builder.rydberg.detuning.uniform.apply(detuning_waveform)
task_builder = task_builder.rabi.amplitude.uniform.apply(rabi_waveform)
task_builder = task_builder.assign(
    initial_detuning=-15,
    final_detuning=10,
    up_time=0.1,
    anneal_time=3,
    rabi_amplitude_max=15,
)

small_program = task_builder.braket_local_simulator(1000)
large_program = task_builder.parallelize(25.0).mock(1000)
large_program.submit()
small_program.submit()

# %%
location.Square(15).rydberg.detuning.uniform.piecewise_linear(
    ["up_time", "anneal_time", "up_time"],
    ["initial_detuning", "initial_detuning", "final_detuning", "final_detuning"],
).rabi.amplitude.uniform.piecewise_linear(
    ["up_time", "anneal_time", "up_time"],
    [0.0, "rabi_amplitude_max", "rabi_amplitude_max", 0.0],
).parallelize(
    20
).assign(
    initial_detuning=-15,
    final_detuning=10,
    up_time=0.1,
    anneal_time=3,
    rabi_amplitude_max=15,
).mock(
    nshots=1000
).submit().report()
