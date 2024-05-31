from collections import OrderedDict, namedtuple
import time
from pydantic.v1.dataclasses import dataclass
import json

from bloqade.builder.typing import LiteralType
from bloqade.ir.routine.base import RoutineBase, __pydantic_dataclass_config__
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.mock import MockBackend
from bloqade.submission.load_config import load_config
from bloqade.task.batch import RemoteBatch
from bloqade.task.quera import QuEraTask

from beartype.typing import Tuple, Union, Optional, NamedTuple, List, Dict, Any
from beartype import beartype
from requests import Response, request


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

    def custom(self) -> "CustomSubmissionRoutine":
        return CustomSubmissionRoutine(self.source, self.circuit, self.params)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class CustomSubmissionRoutine(RoutineBase):
    def _compile(
        self,
        shots: int,
        use_experimental: bool = False,
        args: Tuple[LiteralType, ...] = (),
    ):
        from bloqade.compiler.passes.hardware import (
            analyze_channels,
            canonicalize_circuit,
            assign_circuit,
            validate_waveforms,
            generate_ahs_code,
            generate_quera_ir,
        )
        from bloqade.submission.capabilities import get_capabilities

        circuit, params = self.circuit, self.params
        capabilities = get_capabilities(use_experimental)

        for batch_params in params.batch_assignments(*args):
            assignments = {**batch_params, **params.static_params}
            final_circuit, metadata = assign_circuit(circuit, assignments)

            level_couplings = analyze_channels(final_circuit)
            final_circuit = canonicalize_circuit(final_circuit, level_couplings)

            validate_waveforms(level_couplings, final_circuit)
            ahs_components = generate_ahs_code(
                capabilities, level_couplings, final_circuit
            )

            task_ir = generate_quera_ir(ahs_components, shots).discretize(capabilities)
            MetaData = namedtuple("MetaData", metadata.keys())

            yield MetaData(**metadata), task_ir

    def submit(
        self,
        shots: int,
        url: str,
        json_body_template: str,
        method: str = "POST",
        args: Tuple[LiteralType] = (),
        request_options: Dict[str, Any] = {},
        use_experimental: bool = False,
        sleep_time: float = 0.1,
    ) -> List[Tuple[NamedTuple, Response]]:
        """Compile to QuEraTaskSpecification and submit to a custom service.

        Args:
            shots (int): number of shots
            url (str): url of the custom service
            json_body_template (str): json body template, must contain '{task_ir}'
            which is a placeholder for a string representation of the task ir.
            The task ir string will be inserted into the template with
            `json_body_template.format(task_ir=task_ir_string)`.
            to be replaced by QuEraTaskSpecification
            method (str): http method to be used. Defaults to "POST".
            args (Tuple[LiteralType]): additional arguments to be passed into the
            compiler coming from `args` option of the build. Defaults to ().
            request_options: additional options to be passed into the request method,
            Note the `data` option will be overwritten by the
            `json_body_template.format(task_ir=task_ir_string)`.
            use_experimental (bool): Enable experimental hardware capabilities
            sleep_time (float): time to sleep between each request. Defaults to 0.1.

        Returns:
            List[Tuple[NamedTuple, Response]]: List of parameters for each batch in
            the task and the response from the post request.

        Examples:
            Here is a simple example of how to use this method. Note the body_template
            has double curly braces on the outside to escape the string formatting.

        ```python
        >>> body_template = "{{"token": "my_token", "task": {task_ir}}}"
        >>> responses = (
            program.quera.custom.submit(
                100,
                "http://my_custom_service.com",
                body_template
            )
        )
        ```
        """

        if r"{task_ir}" not in json_body_template:
            raise ValueError(r"body_template must contain '{task_ir}'")

        partial_eval = json_body_template.format(task_ir='"task_ir"')
        try:
            _ = json.loads(partial_eval)
        except json.JSONDecodeError as e:
            raise ValueError(
                "body_template must be a valid json template. "
                'When evaluating template with task_ir="task_ir", '
                f"the template evaluated to: {partial_eval!r}.\n"
                f"JSONDecodeError: {e}"
            )

        out = []
        for metadata, task_ir in self._compile(shots, use_experimental, args):
            json_request_body = json_body_template.format(
                task_ir=task_ir.json(exclude_none=True, exclude_unset=True)
            )
            request_options.update(data=json_request_body)
            response = request(method, url, **request_options)
            out.append((metadata, response))
            time.sleep(sleep_time)

        return out


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class QuEraHardwareRoutine(RoutineBase):
    backend: Union[QuEraBackend, MockBackend]

    def _compile(
        self,
        shots: int,
        use_experimental: bool = False,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
    ) -> RemoteBatch:
        from bloqade.compiler.passes.hardware import (
            analyze_channels,
            canonicalize_circuit,
            assign_circuit,
            validate_waveforms,
            generate_ahs_code,
            generate_quera_ir,
        )

        circuit, params = self.circuit, self.params
        capabilities = self.backend.get_capabilities(use_experimental)

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            assignments = {**batch_params, **params.static_params}
            final_circuit, metadata = assign_circuit(circuit, assignments)

            level_couplings = analyze_channels(final_circuit)
            final_circuit = canonicalize_circuit(final_circuit, level_couplings)

            validate_waveforms(level_couplings, final_circuit)
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
        use_experimental: bool = False,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        """
        Compile to a RemoteBatch, which contain
            QuEra backend specific tasks,
            and run_async through QuEra service.

        Args:
            shots (int): number of shots
            args (Tuple): additional arguments
            name (str): custom name of the batch
            shuffle (bool): shuffle the order of jobs

        Return:
            RemoteBatch

        """
        batch = self._compile(shots, use_experimental, args, name)
        batch._submit(shuffle, **kwargs)
        return batch

    @beartype
    def run(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        use_experimental: bool = False,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        batch = self.run_async(shots, args, name, use_experimental, shuffle, **kwargs)
        batch.pull()
        return batch

    @beartype
    def __call__(
        self,
        *args: LiteralType,
        shots: int = 1,
        name: Optional[str] = None,
        use_experimental: bool = False,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        return self.run(shots, args, name, use_experimental, shuffle, **kwargs)
