from ..base import Builder


class Backend(Builder):
    pass


class LocalBackend(Backend):
    def run(self):
        raise NotImplementedError


class RemoteBackend(Backend):
    def submit(self):
        raise NotImplementedError
