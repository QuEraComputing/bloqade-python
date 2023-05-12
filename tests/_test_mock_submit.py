import bloqade.lattice as lattice
from bloqade.ir import Linear, Constant
from bloqade.task import MockTaskResult
import json

quantum_task = (
    lattice.Square(6)
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
    .assign(
        initial_detuning=-10,
        up_time=0.1,
        final_detuning=15,
        anneal_time=10,
        rabi_amplitude_max=15,
    )
    .program.mock(nshots=10)
    .submit()
)

# print(len(quantum_task.task_result.shot_outputs))

with open("quantum_task.json", "w") as io:
    io.write(quantum_task.json())

with open("quantum_task.json", "r") as io:
    quantum_task = MockTaskResult(**json.load(io))

print(quantum_task.task_result)
