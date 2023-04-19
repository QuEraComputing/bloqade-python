import pytest
from bloqade.ir.scalar import *
import bloqade.ir.real as real

import ast

@bloqade.jit()
def my_pulse(a, b, c):
    x = piecewise_constant(a, b)
    return Sequence(x, x)

ast.braket(a=1, b=2, c=3)

ast = my_pulse(Variable('a'), Variable('b'), Variable('c')) -> Sequence
BloqadeFunction(my_pulse, ast)


def jit(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    ast = fn(Variable('a'), Variable('b'), Variable('c'))
    return BloqadeFunction(wrapper, ast)

my_pulse.simulate(1, 2, 3) # Error
my_pulse.braket(1, 2, 3)

class BloqadeFunction:
    ast: BloqadeIR
    fn: function

    def simulate(self, *args, **kwargs):
        return wrap_to_python(
            convert_to_julia(ast)(args, kwargs)
        )
    
     <-> bloqade python <-> julia
    def braket(self, *args, **kwargs):
        ahs_ir = convert_to_schema(ast)(args, kwargs)
        task = braket.submit(ahs_ir)
        return task


BloqadeSimulator.run(my_pulse, a=1, b=2, c=3)
