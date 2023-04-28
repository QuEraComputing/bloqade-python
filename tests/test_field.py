from bloqade.ir.prelude import *


print(Field({Global: Linear(start=1.0, stop='x', duration=3.0)}))
print(ScaledLocations({1: 1.0, 2: 2.0}))
print(Field({ScaledLocations({1: 1.0, 2: 2.0}): Linear(start=1.0, stop='x', duration=3.0)}))
