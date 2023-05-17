import bloqade.ir.location as location
from bloqade.ir import Linear, Constant
from bloqade.task import HardwareBatch
import numpy as np

builder = (
    location.Square(6)
    .rydberg.detuning.uniform.apply(
        Constant("initial_detuning", "up_time")
        .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
        .append(Constant("final_detuning", "up_time"))
    )
    .rabi.amplitude.uniform.apply(
        Linear(0.0, "rabi_amplitude_max", "up_time")
        .append(Constant("rabi_amplitude_max", "anneal_time"))
        .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
    )
)

tasks = []

for up_time in np.linspace(0.1, 3.8, 51):
    task = builder.assign(
        initial_detuning=-10,
        up_time=up_time,
        final_detuning=15,
        anneal_time=10,
        rabi_amplitude_max=15,
    ).mock(10)

    tasks.append(task)


batch = HardwareBatch(tasks)
batch_future = batch.submit()
results = batch_future.fetch()

print(results)
