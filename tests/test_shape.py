import bloqade.ir.shape as shape
import bloqade.ir.scalar as scalar

s = shape.Linear(scalar.Literal(1.0), scalar.Variable("x"))
print(s.julia())
s = shape.Constant(scalar.Literal(1.0))
print(s.julia())
s = shape.Poly([scalar.Literal(1.0), scalar.Variable("x")])
print(s.julia())
