from bloqade import start

(
    start.add_position((1, 1))
    # .hyperfine.rabi.amplitude.location(1)
    # .rydberg.detuning.location(0)
    .rydberg.rabi.phase.location(1)
    .constant(value=2.0, duration=1.0)
    .constant(value=2.0, duration=1.0)
    .uniform.constant(value=2.0, duration=1.0)
    .assign()
    .flatten(["x"])
    .quera.aquila(nshots=100)
    # .quera.simu(solver='dopri').run()
    # .braket.aquila(nshots=100).submit()
)

prog = (
    start.add_position((1, 1))
    .add_position((2, 2))
    .rydberg.detuning.location(0)
    .location(1)
    .constant(value=1.0, duration=2.0)
    .location(1)
    .constant(value=1.0, duration=3.0)
    .amplitude.location(1)
    .constant(value=1.0, duration=3.0)
    .assign(x=1)  # batch_assign/flatten/*
    .braket(nshots=1000)
)

prog = (
    start.add_position((1, 1))
    .add_position((2, 2))
    .rydberg.detuning.location(1)
    .constant(value=1.0, duration=2.0)
    .location(2)
    .scale(2.0)
    .constant(value=1.0, duration=2.0)
)
