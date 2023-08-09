from ..base import Builder


class Backend(Builder):
    def run(self):
        raise NotImplementedError(
            f"Execution backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


class LocalBackend(Backend):
    pass


class RemoteBackend(Backend):
    # def __init__(self):
    #     self._compile_cache = None

    # NOTE: this is only a sketch, dont use this
    # def __compile__(self):
    #     if self._compile_cache:
    #         return self._compile_cache
    #     from ..compile import to_bloqade_ir, scan_pragma
    #     seq = to_bloqade_ir(self) # -> sequence object
    #     reg = scan_register(self)
    #     self._compile_cache = (seq, reg)
    #     return seq, reg

    # def __compile_assign(self):
    #     assign = self.scan_assign(self) # dict
    #     [replace(self._compile_cache, assign) for each in assign]
    #     return

    def submit(self):
        raise NotImplementedError(
            "Submission backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


class FlattenedBackend(Builder):
    def __call__(self, *args, nshots=1):
        raise NotImplementedError(
            "Flattened backend not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


# class QuEraAquilia(RemoteBackend):

#     def submit(self):
#         seq, reg = self.__compile__(self)
#         target = codegen(seq)
#         return run(target) # -> Futre
#         # return super().submit()
