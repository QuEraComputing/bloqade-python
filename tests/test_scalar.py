import bloqade.ir.scalar as scalar

# x = scalar.Variable("x") + scalar.Variable("y")
# print(x)

# print(-(-scalar.Variable("x")))
# ex = scalar.Variable("x").min(scalar.Literal(1.0)).min(scalar.Literal(2.0))
# print(ex)

x = scalar.Variable("x").add(1.0).add("z").div(2.0)
x.min(scalar.Literal(1.0)).max(scalar.Literal(5.5))

i = scalar.Interval(scalar.Variable("z"), scalar.Literal(5.0))
y = scalar.Slice(x, i)