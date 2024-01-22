from collections import OrderedDict
from pydantic.dataclasses import dataclass
from beartype import beartype
from beartype.typing import Optional, Tuple
from bloqade.core.builder.typing import LiteralType

from bloqade.core.ir.routine.base import RoutineBase, __pydantic_dataclass_config__
from bloqade.core.submission.braket import BraketBackend
from bloqade.core.task.batch import LocalBatch, RemoteBatch
from bloqade.core.task.braket_simulator import BraketEmulatorTask
from bloqade.core.task.braket import BraketTask


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
    """Object to compile and submit tasks to hardware via Braket's API."""

    backend: BraketBackend

    def _compile(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
    ) -> RemoteBatch:
        ## fall passes here ###
        from bloqade.core.compiler.passes.hardware import (
            analyze_channels,
            add_padding,
            assign_circuit,
            validate_waveforms,
            to_literal_and_canonicalize,
            generate_ahs_code,
            generate_quera_ir,
        )

        capabilities = self.backend.get_capabilities()

        circuit, params = self.circuit, self.params

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            assignments = {**batch_params, **params.static_params}
            final_circuit, metadata = assign_circuit(circuit, assignments)

            level_couplings = analyze_channels(final_circuit)
            final_circuit = add_padding(final_circuit, level_couplings)

            validate_waveforms(level_couplings, final_circuit)
            final_circuit = to_literal_and_canonicalize(final_circuit)
            ahs_components = generate_ahs_code(
                capabilities, level_couplings, final_circuit
            )

            task_ir = generate_quera_ir(ahs_components, shots).discretize(capabilities)
            tasks[task_number] = BraketTask(
                None,
                self.backend,
                task_ir,
                metadata,
                ahs_components.lattice_data.parallel_decoder,
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
    ) -> RemoteBatch:
        """Compile and submit a batch of jobs to the device using Braket's API,
        returning immediately after all tasks have been submitted.

        Args:
            shots (int): Number of shots.
            args (Tuple[LiteralType, ...], optional): Value of arguments that where
                differed until runtime via the `args([...])` method.
                The order of the values matches the ordering of the input
                to `args([...])`.
            name (Optional[str], optional): Custom name of the batch
            shuffle (bool, optional): Shuffle the order of jobs

        Return:
            RemoteBatch

        """

        batch = self._compile(shots, args, name)
        batch._submit(shuffle)
        return batch

    @beartype
    def run(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        shuffle: bool = False,
    ) -> RemoteBatch:
        """Compile and submit a batch of jobs to the device using Braket's API,
        waiting for all tasks to reach a terminal state, e.g. failed, canceled
        or completed.

        Args:
            shots (int): Number of shots
            args (Tuple[LiteralType, ...], optional): Value of arguments that where
                differed until runtime via the `args([...])` method.
                The order of the values matches the ordering of the input
                to `args([...])`.
            name (Optional[str], optional): Custom name of the batch
            shuffle (bool, optional): Shuffle the order of jobs

        Return:
            RemoteBatch

        """

        batch = self.run_async(shots, args, name, shuffle)
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
        return self.run(shots, args, name, shuffle, **kwargs)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BraketLocalEmulatorRoutine(RoutineBase):
    """Object to compile and run tasks on Braket's local emulator."""

    def _compile(
        self, shots: int, args: Tuple[LiteralType, ...] = (), name: Optional[str] = None
    ) -> LocalBatch:
        ## fall passes here ###
        from bloqade.core.ir import ParallelRegister
        from bloqade.core.compiler.passes.hardware import (
            analyze_channels,
            add_padding,
            assign_circuit,
            validate_waveforms,
            to_literal_and_canonicalize,
            generate_ahs_code,
            generate_braket_ir,
        )

        circuit, params = self.circuit, self.params

        if isinstance(circuit.register, ParallelRegister):
            raise TypeError(
                "Parallelization of atom arrangements is not supported for "
                "local emulation."
            )

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            assignments = {**batch_params, **params.static_params}
            final_circuit, metadata = assign_circuit(circuit, assignments)

            level_couplings = analyze_channels(final_circuit)
            final_circuit = add_padding(final_circuit, level_couplings)

            validate_waveforms(level_couplings, final_circuit)
            final_circuit = to_literal_and_canonicalize(final_circuit)
            ahs_components = generate_ahs_code(None, level_couplings, final_circuit)
            braket_task_ir = generate_braket_ir(ahs_components, shots)

            tasks[task_number] = BraketEmulatorTask(
                braket_task_ir,
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
        """Compile and run a batch of tasks on Braket's local emulator.

        Args:
            shots (int): Number of shots
            args (Tuple[LiteralType, ...]): Value of arguments that where
                differed until runtime via the `args([...])` method.
                The order of the values matches the ordering of the input
                to `args([...], optional)`.
            name (Optional[str]): Custom name of the batch
            multiprocessing (bool, optional): Run tasks in parallel
            num_workers (Optional[int], optional): Number of workers to use for
                multiprocessing. If None, the number of workers is equal to
                the number of CPU cores.
            **kwargs (Any): Additional keyword arguments to pass to the
                Braket local emulator.

        Return:
            RemoteBatch

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
        return self.run(
            shots,
            args,
            name,
            multiprocessing=multiprocessing,
            num_workers=num_workers,
            **kwargs,
        )
