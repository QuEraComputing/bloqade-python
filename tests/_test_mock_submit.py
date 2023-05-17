import bloqade.ir.location as location
from bloqade.ir import Linear, Constant
from bloqade.task import HardwareTask, HardwareTaskFuture


quantum_task = (
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
    .assign(
        initial_detuning=-10,
        up_time=0.1,
        final_detuning=15,
        anneal_time=10,
        rabi_amplitude_max=15,
    )
    .program.mock(10)
)

# print(len(quantum_task.task_result.shot_outputs))

quantum_task.write_json("quantum_task.json")
quantum_task = HardwareTask()
quantum_task.read_json("quantum_task.json")

# print(quantum_task)

quantum_future = quantum_task.submit()

quantum_future.write_json("quantum_future.json")
quantum_future = HardwareTaskFuture()
quantum_future.read_json("quantum_future.json")
print(quantum_future)
quantum_future.fetch()
print(quantum_future)
