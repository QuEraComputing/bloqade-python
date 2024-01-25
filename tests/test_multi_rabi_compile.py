from bloqade import start
import numpy as np


def test_multi_rabi_compile():
    distance = 4.0

    # Example defaults to option 7
    geometry = start.add_position(
        [
            (0, 0),
            (distance, 0),
            (-0.5 * distance, distance),
            (0.5 * distance, distance),
            (1.5 * distance, distance),
            (0, 2 * distance),
            (distance, 2 * distance),
        ]
    )

    sequence = start.rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=["ramp_time", "run_time", "ramp_time"],
        values=[0.0, "rabi_drive", "rabi_drive", 0.0],
    ).parse_sequence()

    batch = (
        geometry.apply(sequence)
        .assign(ramp_time=0.06, rabi_drive=5)
        .batch_assign(run_time=0.05 * np.arange(21))
    )

    bloqade_emu_target = batch.bloqade.python()
    braket_emu_target = batch.braket.local_emulator()
    quera_aquila_target = batch.parallelize(24).quera.aquila()
    braket_aquila_target = batch.parallelize(24).braket.aquila()

    targets = [
        bloqade_emu_target,
        braket_emu_target,
        quera_aquila_target,
        braket_aquila_target,
    ]

    for target in targets:
        target._compile(10)
