from abc import ABC
import numpy as np
import bloqade
from bloqade import start
import json
from bloqade.builder.emit import Emit

class Ansatz(ABC):

    def __init__(self, backend_info):
        self._job_tape = {}
        self._backend_info = backend_info

    def ansatz(self, **kwargs)->Emit:
        return start

    def submit(self, quantum_parameters):
        if isinstance(quantum_parameters, np.ndarray):
            quantum_parameters = quantum_parameters.tolist()

        key = str(quantum_parameters)
        if key in self._job_tape:
            return self._job_tape[key]

        backend_names = ["classical_simulator", "quantum_braket", "quantum_quera_internal"]

        # Create job depending on backend
        if self._backend_info["backend"] == backend_names[0]:
            job = self.ansatz(quantum_parameters).braket_local_simulator(self._backend_info["num_shots"])
        elif self._backend_info["backend"] == backend_names[1]:
            job = self.ansatz(quantum_parameters).braket(self._backend_info["num_shots"])
        elif self._backend_info["backend"] == backend_names[2]:
            job = self.ansatz(quantum_parameters).quera(self._backend_info["num_shots"], config_file=self._backend_info["config_path"])
        else:
            raise BaseException(f"Not a valid backend! Valid backends are {backend_names}")
        
        submitted_job = job.submit()
        self._job_tape[key] = submitted_job

        self._to_file(filename=f"submitted_jobs_tape.json")

        return submitted_job

    def get_bitstrings(self, quantum_parameters):
        job = self.submit(quantum_parameters)
        return np.array(job.report().bitstrings[0])

    def _to_file(self, filename):
        payload = {key: job.json() for key, job in self._job_tape.items()}
        with open(filename, "w") as io:
            json.dump(payload, io)

    def _from_file(self, filename):
        with open(filename, "w") as io:
            payload = json.load(io)
        self._job_tape = {key: bloqade.load(val) for key, val in payload.items()}
