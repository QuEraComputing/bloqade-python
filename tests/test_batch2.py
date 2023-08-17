import bloqade.ir.location as location
from bloqade.ir import Linear, Constant
import numpy as np

task = (
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
    .assign(initial_detuning=-10, up_time=0.1, anneal_time=3.8, rabi_amplitude_max=15)
    .batch_assign(final_detuning=np.linspace(0, 10, 51))
    .quera.mock(100)
)
future = task.submit()
print(future.report())
