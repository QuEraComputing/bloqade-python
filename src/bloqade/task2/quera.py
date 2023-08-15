from bloqade.task2.base import Geometry
from .base import Task, JSONInterface
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.quera import QuEraBackend
from typing import Optional
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.base import ValidationError
from bloqade.submission.ir.task_results import QuEraTaskResults, QuEraTaskStatusCode
import warnings


class QuEraTask(Task, JSONInterface):
    task_ir: Optional[QuEraTaskSpecification]
    backend: QuEraBackend
    task_result_ir: Optional[QuEraTaskResults]
    parallel_decoder: Optional[ParallelDecoder]

    def __init__(
        self,
        task_ir: QuEraTaskSpecification,
        task_id: str = None,
        backend: QuEraBackend = None,
        parallel_decoder: Optional[ParallelDecoder] = None,
        **kwargs,
    ):
        super().__init__(
            task_id=task_id,
        )
        self.task_ir = task_ir
        self.backend = backend
        self.task_id = task_id
        self.parallel_decoder = parallel_decoder

    def submit(self, force: bool = False) -> None:
        if not force:
            if self.task_id is not None:
                raise ValueError(
                    "the task is already submitted with %s" % (self.task_id)
                )

        self.task_id = self.backend.submit_task(self.task_ir)

    def validate(self) -> str:
        try:
            self.backend.validate_task(self.task_ir)
        except ValidationError as e:
            return str(e)

    def fetch(self) -> None:
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        self.task_result_ir = self.backend.task_results(self.task_id)

    def result(self) -> QuEraTaskResults:
        if self.task_result_ir is None:
            self.fetch()

        return self.task_result_ir

    def status(self) -> QuEraTaskStatusCode:
        return self.backend.task_results(self.task_id)

    def cancel(self) -> None:
        if self.task_id is None:
            warnings.warn("Cannot cancel task, missing task id.")
            return

        self.backend.cancel_task(self.task_id)

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.lattice.sites,
            filling=self.task_ir.lattice.filling,
            parallel_decoder=self.parallel_decoder,
        )

    # def submit_no_task_id(self) -> "HardwareTaskShotResults":
    #    return HardwareTaskShotResults(hardware_task=self)


# class QuEraBatch(Batch, JSONInterface):
#    #futures: List[QuEraTask]
#    pass
