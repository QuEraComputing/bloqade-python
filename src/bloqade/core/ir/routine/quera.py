from collections import OrderedDict
from pydantic.dataclasses import dataclass
import json

from bloqade.core.builder.typing import LiteralType
from bloqade.core.ir.routine.base import RoutineBase, __pydantic_dataclass_config__
from bloqade.core.submission.quera import QuEraBackend
from bloqade.core.submission.mock import MockBackend
from bloqade.core.submission.load_config import load_config
from bloqade.core.task.batch import RemoteBatch
from bloqade.core.task.quera import QuEraTask

from beartype.typing import Tuple, Union, Optional
from beartype import beartype


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class QuEraServiceOptions(RoutineBase):
    @beartype
    def device(self, config_file: Optional[str], **api_config):
        if config_file is not None:
            with open(config_file, "r") as f:
                api_config = {**json.load(f), **api_config}

        backend = QuEraBackend(**api_config)

        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)

    def aquila(self) -> "QuEraHardwareRoutine":
        backend = QuEraBackend(**load_config("Aquila"))
        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)

    def cloud_mock(self) -> "QuEraHardwareRoutine":
        backend = QuEraBackend(**load_config("Mock"))
        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)

    @beartype
    def mock(
        self, state_file: str = ".mock_state.txt", submission_error: bool = False
    ) -> "QuEraHardwareRoutine":
        backend = MockBackend(state_file=state_file, submission_error=submission_error)
        return QuEraHardwareRoutine(self.source, self.circuit, self.params, backend)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class QuEraHardwareRoutine(RoutineBase):
    """Object for compiling and submitting tasks to hardware via QuEra's API."""

    backend: Union[QuEraBackend, MockBackend]

    def _compile(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
    ) -> RemoteBatch:
        from bloqade.core.compiler.passes.hardware import (
            analyze_channels,
            add_padding,
            assign_circuit,
            validate_waveforms,
            to_literal_and_canonicalize,
            generate_ahs_code,
            generate_quera_ir,
        )

        circuit, params = self.circuit, self.params
        capabilities = self.backend.get_capabilities()

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

            tasks[task_number] = QuEraTask(
                None,
                self.backend,
                task_ir,
                metadata,
                ahs_components.lattice_data.parallel_decoder,
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
        """Compile and submit a batch of jobs to the device using QuEra's API,
        returning immediately after all tasks have been submitted.

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
        **kwargs,
    ) -> RemoteBatch:
        """Compile and submit a batch of jobs to the device using QuEra's API,
        waiting for all tasks to reach a terminal state, e.g. failed, canceled
        or completed.

        Args:
            shots (int): number of shots
            args (Tuple[LiteralType, ...], optional): Value of arguments that where
                differed until runtime via the `args([...])` method.
                The order of the values matches the ordering of the input
                to `args([...])`.
            name (Optional[str], optional): custom name of the batch
            shuffle (bool, optional): shuffle the order of jobs

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
    ) -> RemoteBatch:
        return self.run(shots, args, name, shuffle, **kwargs)
