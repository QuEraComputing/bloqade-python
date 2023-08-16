from itertools import repeat
from typing import Dict, Tuple
import numbers

from ... import ir
from ..base import Builder
from ..compile.trait import CompileProgram
from ..compile.stream import BuilderStream, BuilderNode
from ...task2.batch import RemoteBatch, LocalBatch


class Backend(Builder, CompileProgram):
    def __init__(
        self, cache_compiled_programs: bool = False, parent: Builder | None = None
    ) -> None:
        super().__init__(parent)
        self._static_ir_cache = None
        self._batch_ir_cache = []
        self._cluster_spacing = None
        self._static_params = {}
        self._batch_params = {}
        self._orders = ()
        self._cache = cache_compiled_programs

    def _mappings(self, *args: numbers.Real):
        input_mapping = self._parse_args(*args)

        if self._batch_params:
            batch_iterators = [
                zip(repeat(name), values) for name, values in self._batch_params.items()
            ]

            return (
                {**input_mapping, **dict(tuples)} for tuples in zip(*batch_iterators)
            )
        else:
            return (input_mapping,)

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

    def _compile_static(self) -> ir.Program:
        from ...codegen.common.static_assign import StaticAssignProgram

        if self._cache and self._static_ir_cache:
            return self._static_ir_cache

        if self._cache:
            program = self.compile_program(**self._static_params)
            self._static_ir_cache = StaticAssignProgram(self._static_params).emit(
                program
            )
            return self._static_ir_cache
        else:
            program = self.compile_program(**self._static_params)
            return StaticAssignProgram(self._static_params).emit(program)

    def _compile_batch(self, *args):
        from ...codegen.common.static_assign import StaticAssignProgram

        if self._cache and self._batch_ir_cache:
            return self._batch_ir_cache

        if self._cache:
            for mapping in self._mappings(*args):
                self._batch_ir_cache.append(
                    (
                        mapping,
                        StaticAssignProgram(mapping).emit(self._static_ir_cache()),
                    )
                )
        else:
            self._static_ir_cache = (
                (mapping, StaticAssignProgram(mapping).emit(self._static_ir_cache()))
                for mapping in self._mappings(*args)
            )

        return self._batch_ir_cache

    def _compile_ir(self, *args: Tuple[numbers.Real, ...]):
        self._compile_builder()
        self._compile_static()
        return self._compile_batch(*args)

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
        batch = LocalBatch(tasks)

        return batch


class RemoteBackend(Backend):
    def __call__(self, *args, shots: int = 1):
        batch = self.submit()
        batch.pull()  # blocking
        return batch

    def submit(self, *args, shots: int = 1, name=None, shuffle=False):
        tasks = [
            self._compile_task(program, shots, **metadata)
            for metadata, program in self._compile_ir(*args)
        ]
        batch = RemoteBatch(dict(zip(range(len(tasks)), tasks)), name)

        batch._submit(self, shuffle_submit_order=shuffle)

        return batch
