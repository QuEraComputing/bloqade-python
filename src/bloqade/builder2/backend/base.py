from typing import List
from ..base import Builder

# from ... import ir

from ..compile.trait import Compile
from ..compile.stream import BuilderStream


class Backend(Builder, Compile):
    def __init__(self, parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._ir_cache = None

    def __compile_ir__(self):
        from ..assign import Assign

        if self._ir_cache:
            return self._ir_cache

        stream = BuilderStream(self)
        assign_options = stream.eat([Assign])

        if assign_options is not None:
            assignments = assign_options.node._assignments
        else:
            assignments = {}

        self._ir_cache = self.compile_bloqade_ir(**assignments)
        return self._ir_cache

    def compile(self):
        raise NotImplementedError(
            "Compilation backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


class LocalBackend(Backend):
    def __call__(self):
        raise NotImplementedError(
            "__call__ backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


class RemoteBackend(Backend):
    def __init__(self, parent: Builder | None = None) -> None:
        super().__init__(parent)

    def __call__(self):
        batch = self.submit()
        batch.fetch()
        return batch

    def submit(self):
        raise NotImplementedError(
            "Submission backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


class FlattenedBackend(Backend):
    def __init__(self, arg_list: List[str], parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._arg_list = arg_list

    def __call__(self, *args, nshots=1):
        raise NotImplementedError(
            "__call__ backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )
