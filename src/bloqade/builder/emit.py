from .base import Builder


class Emit(Builder):
    # NOTE: this will mutate the builder
    # because once methods inside this class are called
    # the building process will terminate
    # none of the methods in this class will return a Builder

    def __init__(self, builder: Builder) -> None:
        super().__init__(builder)
        self.__assignments = None

    def assign(self, **assignments):
        self.assignments = assignments
        return self

    @property
    def sequence(self):
        # build the Sequence object
        pass

    def quera(self):  # -> return QuEraSchema object
        pass

    def braket(self):  # -> return BraketSchema object
        pass

    def simu(self):  # -> Simulation object
        pass
