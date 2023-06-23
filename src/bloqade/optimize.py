from collections import OrderedDict
from bloqade.codegen.hardware.quera import SchemaCodeGen
from bloqade.ir.program import Program
from bloqade.submission.base import SubmissionBackend
from bloqade.submission.ir.braket import to_braket_task_ir
from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.task import Task
from pydantic import BaseModel
from typing import Callable, Dict, List, Optional
from bloqade.task.base import Future, Report, Job

from bloqade.task.hardware import HardwareJob, HardwareTask
from bloqade.task.braket_simulator import BraketEmulatorJob, BraketEmulatorTask


def default_optimizer():
    raise NotImplementedError


class JobGenerator(BaseModel):
    program: Program
    static_assignments: Dict[str, float]

    class Config:
        arbitrary_types_allowed = True

    def generate_job(
        self, nshots: int, batch_assignments: List[Dict[str, float]]
    ) -> Job:
        raise NotImplementedError

    def submit(self, nshots: int, batch_assignments: List[Dict[str, float]]) -> Future:
        return self.generate_job(
            nshots=nshots, batch_assignments=batch_assignments
        ).submit()

    def optimize(
        self,
        nshots: int,
        cost_function: Callable[Report, float],
        optimizer=default_optimizer(),
    ) -> "TaskOptimizer":
        return TaskOptimizer(nshots, self, cost_function, optimizer)


class HardwareTaskGenerator(JobGenerator):
    backend: SubmissionBackend
    capabilities: Optional[QuEraCapabilities]

    def __init__(
        self,
        program: Program,
        static_assignments: Dict[str, float],
        backend: SubmissionBackend,
    ):
        capabilities = backend.get_capabilities()
        super().__init__(
            program=program,
            static_assignments=static_assignments,
            capabilities=capabilities,
            backend=backend,
        )

    def generate_task(self, nshots: int, **assignments) -> Task:
        assignments = {**self.static_assignments, **assignments}
        schema_compiler = SchemaCodeGen(
            assignments=assignments, capabilities=self.capabilities
        )
        task_ir = schema_compiler.emit(nshots=nshots, program=self.program)
        return HardwareTask(
            task_ir=task_ir,
            backend=self.backend,
            parallel_decoder=schema_compiler.parallel_decoder,
        )

    def generate_job(
        self, nshots: int, batch_assignments: List[Dict[str, float]]
    ) -> HardwareJob:
        tasks = OrderedDict()
        for i, assignments in enumerate(batch_assignments):
            tasks[i] = self.generate_task(nshots=nshots, assignments=assignments)

        return HardwareJob(tasks=tasks)


class BraketSimulatorTaskGenerator(JobGenerator):
    def __init__(
        self,
        program: Program,
        static_assignments: Dict[str, float],
    ):
        super().__init__(
            program=program,
            static_assignments=static_assignments,
        )

    def generate_task(self, nshots: int, assignments: Dict[str, float]) -> Task:
        assignments = {**self.static_assignments, **assignments}
        schema_compiler = SchemaCodeGen(
            assignments=assignments, capabilities=self.capabilities
        )
        task_ir = schema_compiler.emit(nshots=nshots, program=self.program)
        return BraketEmulatorTask(task_ir=to_braket_task_ir(task_ir))

    def generate_job(
        self, nshots: int, batch_assignments: List[Dict[str, float]]
    ) -> BraketEmulatorJob:
        tasks = OrderedDict()
        for i, assignments in enumerate(batch_assignments):
            tasks[i] = self.generate_task(nshots=nshots, assignments=assignments)

        return BraketEmulatorJob(tasks=tasks)


# A class that takes the TaskGenerator as well as a cost function callable
# returns the the best task
class TaskOptimizer:
    def __init__(
        self,
        nshots: int,
        task_generator: JobGenerator,
        cost_function: Callable,
        optimizer,
    ):
        self.nshots = nshots
        self.task_generator = task_generator
        self.cost_function = cost_function
        self.optimizer = optimizer

    def map_param_to_dict(self, param: List[List[float]]) -> List[Dict[str, float]]:
        # TODO: map a list to a dictionary
        raise NotImplementedError

    def cost_function(self, params: List[List[float]]):
        # evaluates the cost function for a list of parameters
        job = self.task_generator.generate_job(
            nshots=self.nshots, batch_assignments=self.map_param_to_dict(params)
        )
        return self.cost_function(job.submit().report())
