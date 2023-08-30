import bloqade.ir.location as location
from bloqade.ir import Linear, Constant

quantum_job = (
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
    .quera.mock()
    .compile(shots=10)
)

# print(len(quantum_task.task_result.shot_outputs))
# job_file = tempfile.mktemp(suffix=".json")

# quantum_job.save_json(job_file)
# quantum_job = HardwareBatchTask.load_json(job_file)

# future_file = tempfile.mktemp(suffix=".json")
# quantum_future = quantum_job.submit()
# quantum_future.save_json(future_file)
# quantum_future = HardwareBatchResult.load_json(future_file)

# quantum_future.json()
# quantum_future.task_results
