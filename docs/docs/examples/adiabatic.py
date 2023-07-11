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
from bloqade.ir import Sequence, rydberg, detuning, rabi, Uniform, Linear, Constant

# %% [markdown]
# split up waveform construction

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

task_builder = location.Square(6)
task_builder = task_builder.rydberg.detuning.uniform.apply(detuning_waveform)
task_builder = task_builder.rabi.amplitude.uniform.apply(rabi_waveform)
task_builder = task_builder.assign(
    initial_detuning=-15,
    final_detuning=10,
    up_time=0.1,
    anneal_time=10,
    rabi_amplitude_max=15,
)
# stop building for small task
small_program = task_builder.braket_local_simulator(1000)

# continue constructing larger task
large_program = task_builder.parallelize(25.0).mock(1000)

# single task
small_program.submit()

# parallelized task
large_program.submit()


# %%
location.Square(6).rydberg.detuning.uniform.apply(
    Constant("initial_detuning", "up_time")
    .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
    .append(Constant("final_detuning", "up_time"))
).rabi.amplitude.uniform.apply(
    Linear(0.0, "rabi_amplitude_max", "up_time")
    .append(Constant("rabi_amplitude_max", "anneal_time"))
    .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
).parallelize(
    20
).assign(
    initial_detuning=-15,
    final_detuning=10,
    up_time=0.1,
    anneal_time=10,
    rabi_amplitude_max=15,
).mock(
    nshots=1000
).submit().report()

# %% [markdown]
# dict interface (only used by developmenet team)

# %%
seq = Sequence(
    {
        rydberg: {
            detuning: {
                Uniform: Constant("initial_detuning", "up_time")
                .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
                .append(Constant("final_detuning", "up_time")),
            },
            rabi.amplitude: {
                Uniform: Linear(0.0, "rabi_amplitude_max", "up_time")
                .append(Constant("rabi_amplitude_max", "anneal_time"))
                .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
            },
        }
    }
)

# %%
location.Square(6).apply(seq).braket(nshots=1000).submit(token="112312312").report()

# %%
print(seq)
