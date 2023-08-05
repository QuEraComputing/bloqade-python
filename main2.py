from bloqade import start

prog = (
    start.add_position((1, 1))
    # .hyperfine.rabi.amplitude.location(1)
    # .rydberg.detuning.location(0)
    .rydberg.rabi.phase.location(1)
    .constant(value=2.0, duration=1.0)
    .constant(value=2.0, duration=1.0)
    .uniform.constant(value=2.0, duration=1.0)
    .assign()
    .flatten(["x"])
    .device("bloqade.python", solver="dopri5")
    # .bloqade.python(solver="dopri5")
    # .device('quera.aquila', nshots=100)
    # .quera.aquila(nshots=100)
    # .quera.simu(solver='dopri').run()
    # .braket.aquila(nshots=100).submit()
)

print(prog)
