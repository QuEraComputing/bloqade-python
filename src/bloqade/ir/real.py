from dataclasses import dataclass


class Real:
    pass

@dataclass(frozen=True)
class Literal(Real):
    value: float

    def julia_adt(self):
        return NotImplemented
        # return ir_types.Literal(self.value)

@dataclass(frozen=True)
class Variable(Real):
    name: str  # TODO: use a token so we have O(1) comparision
    
    def julia_adt(self):
        return NotImplemented
        # return  ir_types.Variable(self.name)
