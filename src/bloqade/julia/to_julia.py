from juliacall import AnyValue  # type: ignore

class ToJulia:
    def __init__(self, value):
        self.value = value

    def julia(self) -> AnyValue:
        raise NotImplementedError
