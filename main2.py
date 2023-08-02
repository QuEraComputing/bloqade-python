from bloqade import start

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
