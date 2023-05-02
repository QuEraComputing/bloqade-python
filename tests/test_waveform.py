from bloqade.ir.prelude import *

wf = Linear(start=1.0, stop="x", duration=3.0)
# wf = Constant(value=1.0, duration=3.0)
print(wf[:0.5].duration)
print(wf[1.0:].duration)
print(wf[0.2:0.8].duration)

print(-wf)

# canonicalize append
wf = (Linear(0.0, "rabi_amplitude_max", "up_time")
    .append(Constant("rabi_amplitude_max", "anneal_time"))
    .append(Linear("rabi_amplitude_max", 0.0, "up_time")))


print(wf)
wf = wf.append(wf)

print(wf)
