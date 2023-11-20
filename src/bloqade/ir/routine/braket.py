from collections import OrderedDict
from pydantic.dataclasses import dataclass
from beartype import beartype
from beartype.typing import Optional, Tuple
from bloqade.builder.typing import LiteralType

from bloqade.ir.routine.base import RoutineBase, __pydantic_dataclass_config__
from bloqade.submission.braket import BraketBackend
from bloqade.task.batch import LocalBatch, RemoteBatch
from bloqade.task.braket_simulator import BraketEmulatorTask
from bloqade.task.braket import BraketTask


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BraketServiceOptions(RoutineBase):
    def device(self, device_arn: str) -> "BraketHardwareRoutine":
        backend = BraketBackend(device_arn=device_arn)
        return BraketHardwareRoutine(self.source, self.circuit, self.params, backend)

    def aquila(self) -> "BraketHardwareRoutine":
        backend = BraketBackend(
            device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
        )
        return BraketHardwareRoutine(self.source, self.circuit, self.params, backend)

    def local_emulator(self):
        return BraketLocalEmulatorRoutine(self.source, self.circuit, self.params)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BraketHardwareRoutine(RoutineBase):
    backend: BraketBackend

    def _compile(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
    ) -> RemoteBatch:
        ## fall passes here ###
        from bloqade.transform.common.assign_variables import AssignBloqadeIR
        from bloqade.analysis.common.assignment_scan import AssignmentScan
        from bloqade.codegen.hardware.quera import AHSCodegen

        capabilities = self.backend.get_capabilities()

        circuit, params = self.circuit, self.params
        circuit = AssignBloqadeIR(params.static_params).visit(circuit)

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            record_params = AssignmentScan(batch_params).emit(circuit)
            final_circuit = AssignBloqadeIR(record_params).visit(circuit)
            # TODO: Replace these two steps with:
            # task_ir, parallel_decoder = BraketCodeGen().emit(shots, final_circuit)
            result = AHSCodegen(shots, capabilities=capabilities).emit(final_circuit)
            metadata = {**params.static_params, **record_params}
            task_ir = result.quera_task_ir.discretize(capabilities)
            tasks[task_number] = BraketTask(
                None,
                self.backend,
                task_ir,
                metadata,
                result.parallel_decoder,
                None,
            )

        batch = RemoteBatch(source=self.source, tasks=tasks, name=name)

        return batch

    @beartype
    def run_async(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        """
        Compile to a RemoteBatch, which contain
        Braket backend specific tasks, and run_async to Braket.

        Note:
            This is async.

        Args:
            shots (int): number of shots
            args (Tuple): Values of the parameter defined in `args`, defaults to ()
            name (str | None): custom name of the batch, defaults to None
            shuffle (bool): shuffle the order of jobs

        Return:
            RemoteBatch

        """

        batch = self._compile(shots, args, name)
        batch._submit(shuffle, **kwargs)
        return batch

    @beartype
    def run(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        """
        Compile to a RemoteBatch, which contain
        Braket backend specific tasks, run_async to Braket,
        and wait until the results are coming back.

        Note:
            This is sync, and will wait until remote results
            finished.

        Args:
            shots (int): number of shots
            args (Tuple): additional arguments
            name (str): custom name of the batch
            shuffle (bool): shuffle the order of jobs

        Return:
            RemoteBatch

        """

        batch = self.run_async(shots, args, name, shuffle, **kwargs)
        batch.pull()
        return batch

    @beartype
    def __call__(
        self,
        *args: LiteralType,
        shots: int = 1,
        name: Optional[str] = None,
        shuffle: bool = False,
        **kwargs,
    ):
        """
        Compile to a RemoteBatch, which contain
        Braket backend specific tasks, run_async to Braket,
        and wait until the results are coming back.

        Note:
            This is sync, and will wait until remote results
            finished.

        Args:
            shots (int): number of shots
            args: additional arguments for args variables.
            name (str): custom name of the batch
            shuffle (bool): shuffle the order of jobs

        Return:
            RemoteBatch

        """
        return self.run(shots, args, name, shuffle, **kwargs)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BraketLocalEmulatorRoutine(RoutineBase):
    def _compile(
        self, shots: int, args: Tuple[LiteralType, ...] = (), name: Optional[str] = None
    ) -> LocalBatch:
        ## fall passes here ###
        from bloqade.ir import ParallelRegister
        from bloqade.transform.common.assign_variables import AssignBloqadeIR
        from bloqade.analysis.common.assignment_scan import AssignmentScan
        from bloqade.codegen.hardware.quera import AHSCodegen

        circuit, params = self.circuit, self.params
        circuit = AssignBloqadeIR(params.static_params).visit(circuit)

        if isinstance(circuit.register, ParallelRegister):
            raise TypeError(
                "Parallelization of atom arrangements is not supported for "
                "local emulation."
            )

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            record_params = AssignmentScan(batch_params).emit(circuit)
            final_circuit = AssignBloqadeIR(record_params).visit(circuit)
            # TODO: Replace these two steps with:
            # task_ir, _ = BraketCodeGen().emit(shots, final_circuit)
            result = AHSCodegen(shots).emit(final_circuit)

            metadata = {**params.static_params, **record_params}
            tasks[task_number] = BraketEmulatorTask(
                result.braket_task_ir,
                metadata,
                None,
            )

        batch = LocalBatch(source=self.source, tasks=tasks, name=name)

        return batch

    @beartype
    def run(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        **kwargs,
    ) -> LocalBatch:
        """
        Compile to a LocalBatch, and run.
        The LocalBatch contain tasks to run on local emulator.

        Note:
            This is sync, and will wait until remote results
            finished.

        Args:
            shots (int): number of shots
            args: additional arguments for args variables.
            multiprocessing (bool): enable multi-process
            num_workers (int): number of workers to run the emulator

        Return:
            LocalBatch

        """

        batch = self._compile(shots, args, name)
        batch._run(multiprocessing=multiprocessing, num_workers=num_workers, **kwargs)
        return batch

    @beartype
    def __call__(
        self,
        *args: LiteralType,
        shots: int = 1,
        name: Optional[str] = None,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        **kwargs,
    ):
        """
        Compile to a LocalBatch, and run.
        The LocalBatch contain tasks to run on local emulator.

        Note:
            This is sync, and will wait until remote results
            finished.

        Args:
            shots (int): number of shots
            args: additional arguments for args variables.
            multiprocessing (bool): enable multi-process
            num_workers (int): number of workers to run the emulator

        Return:
            LocalBatch

        """
        return self.run(
            shots,
            args,
            name,
            multiprocessing=multiprocessing,
            num_workers=num_workers,
            **kwargs,
        )
