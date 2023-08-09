from bloqade import start
from bloqade.builder2.compile import PulseCompiler


prog = (
    start.add_position((1, 1))
    # .hyperfine.rabi.amplitude.location(1)
    # .rydberg.detuning.location(0)
    # .rydberg.rabi.phase
    .rydberg.detuning.uniform.constant(value=2.0, duration=1.0)
    .rydberg.rabi.amplitude.location(0)
    .location(1)
    .scale(2.0)
    .constant(value=1.0, duration=2.0)
    .hyperfine.rabi.amplitude.location(0)
    .location(1)
    .scale(2.0)
    .constant(value=2.0, duration=1.0)
    .detuning.uniform.linear(0, 1, 1.5)
    .var("x")
    .linear("a", "B", "C")
    # .constant(value=2.0, duration=1.0)
    # .uniform.constant(value=2.0, duration=1.0)
    # .assign()
    # .flatten(["x"])
    # .device("bloqade.python", solver="dopri5")
    # .bloqade.python(solver="dopri5")
    # .device('quera.aquila', nshots=100)
    # .quera.aquila(nshots=100)
    # .quera.simu(solver='dopri').run()
    # .braket.aquila(nshots=100).submit()
)


pc = PulseCompiler(prog)

sequence = pc.compile()

print(repr(sequence))
