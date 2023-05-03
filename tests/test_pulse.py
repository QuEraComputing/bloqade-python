from bloqade.ir import Field, Uniform, Linear, Pulse, detuning, rabi

f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})

print(Pulse({detuning: f}))
print(Pulse({rabi.amplitude: f}))
print(Pulse({rabi.phase: f}))
print(Pulse({detuning: {Uniform: Linear(start=1.0, stop="x", duration=3.0)}}))
