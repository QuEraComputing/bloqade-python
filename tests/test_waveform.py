from bloqade.ir.prelude import *

wf = Linear(start=1.0, stop="x", duration=3.0)
# wf = Constant(value=1.0, duration=3.0)
print(wf[:0.5].duration)
print(wf[1.0:].duration)
print(wf[0.2:0.8].duration)

print(-wf)
