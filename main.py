from pydantic.dataclasses import dataclass
from pydantic import BaseModel
from typing import Any, Optional





class ScalarInterpreter:
    assignments: Dict[scalar.Variable, FloatType]
    
    
    
    def emit(self, scalar_expr: scalar.Scalar):
        match scalar_expr:
            case scalar.Literal(value):
                return float(value)
            case scalar.Variable(name):
                return  float(self.assignments[name])
            case scalar.Add(lhs, rhs):
                return self.emit(lhs) + self.emit(rhs)    


class Scalar:

    def __call__(self, assigns: dict) -> Any:
        ScalarInterp(self, assigns).run(*args, **kwds)

@dataclass(frozen=True)
class Real:
    value: float

@dataclass(frozen=True)
class Add:
    lhs: Scalar
    rhs: Scalar

@dataclass(frozen=True)
class Variable(Scalar):
    name: str

class ScalarInterp:
    ast: Scalar
    assigns: dict[str, float]

    def run(self, *args: Any, **kwds: Any) -> Any:
        # do some toplevel analysis
        # store the state
        self.ast.__call__()
                

class RealInterp(ScalarInterp):

    def __init__(self) -> None:
        super().__init__()
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        super().__call__(*args, **kwds)



@dataclass
class MixinState:
    value: Optional[str] = None


class Mixin:
    def my_trait(self, state: MixinState):
        return NotImplemented

class ADT(Mixin):
    pass

@dataclass(frozen=True)
class SubClass(ADT):
    def my_trait(self, state: MixinState):
        print(state.value)

@dataclass(frozen=True)
class SuperClass(ADT):
    sub_class: SubClass
    
    def my_trait(self, state: MixinState):
        state.value = "message to propagate"
        self.sub_class.my_trait(state)
       

sub_class = SubClass()
super_class = SuperClass(sub_class = sub_class)   


mixin_state = MixinState()
super_class.my_trait(mixin_state)
    

