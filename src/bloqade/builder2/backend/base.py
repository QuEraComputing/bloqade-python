from itertools import repeat
from typing import Dict
import numbers

from ... import ir
from ..base import Builder
from ..compile.trait import Compile
from ..compile.stream import BuilderStream, BuilderNode
from ...task2.base import Batch


class Backend(Builder, Compile):
    def __init__(self, cache: bool = False, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._ir_cache = None
        self._cluster_spacing = None
        self._static_params = {}
        self._batch_params = {}
        self._orders = ()
        self._cache = cache

    def _parse_args(self, *args: numbers.Real) -> Dict[str, float]:
        if len(args) != len(self._orders):
            raise ValueError(
                f"Number of arguments ({len(args)}) does not match "
                f"number of flattened variables ({len(self._orders)})."
            )

        return dict(zip(self._orders, map(float, args)))

    def _compile_builder(self) -> None:
        from ..assign import Assign, BatchAssign
        from ..flatten import Flatten
        from ..parallelize import Parallelize, ParallelizeFlatten

        stream = BuilderStream(self)

        while stream.curr is not None:
            node = stream.read_next(
                [Assign, BatchAssign, Flatten, ParallelizeFlatten, Parallelize]
            )
            match node:
                case BuilderNode(node=Assign(static_params)):
                    self._static_params = static_params
                case BuilderNode(node=BatchAssign(batch_params)):
                    self._batch_params = batch_params
                case BuilderNode(node=Parallelize(cluster_spacing)) | BuilderNode(
                    node=ParallelizeFlatten(cluster_spacing)
                ):
                    self._cluster_spacing = cluster_spacing
                case BuilderNode(node=Flatten(orders)):
                    self._orders = orders

    def _compile_cache(self) -> ir.Program:
        if self._ir_cache:
            return self._ir_cache

        self._ir_cache = self.compile_bloqade_ir(**self._static_params)

        return self._ir_cache

    def _compile_ir(self, *args):
        from ...codegen.common.static_assign import StaticAssignProgram

        self._compile_builder()
        ir_cache = self._compile_cache()

        input_mapping = self._parse_args(*args)

        if self._batch_params:
            batch_iterators = [
                zip(repeat(name), values) for name, values in self._batch_params.items()
            ]

            mappings = (
                {**input_mapping, **dict(tuples)} for tuples in zip(*batch_iterators)
            )

            for mapping in mappings:
                yield mapping, StaticAssignProgram(mapping).emit(ir_cache)
        else:
            yield input_mapping, ir_cache

    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        raise NotImplementedError(
            "Compilation not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


class LocalBackend(Backend):
    def __call__(self, *args, shots: int = 1):
        tasks = [
            self._compile_task(program, shots, **metadata)
            for metadata, program in self._compile_ir(*args)
        ]
        batch = Batch(tasks)

        return batch


class RemoteBackend(Backend):
    def __call__(self, *args, shots: int = 1):
        batch = self.submit()
        batch.fetch()
        return batch

    def submit(self, *args, shots: int = 1):
        raise NotImplementedError(
            "Submission backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )
