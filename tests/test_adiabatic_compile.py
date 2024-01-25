from bloqade import start, cast, var
import numpy as np


def test_adiabatic_compile():
    detuning_value = var("detuning_value")
    durations = cast(["ramp_time", "run_time", "ramp_time"])
    prog = (
        start.add_position([(0, 0), (0, "atom_distance")])
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=durations, values=[0, "rabi_value", "rabi_value", 0]
        )
        .detuning.uniform.piecewise_linear(
            durations=durations,
            values=[
                -detuning_value,
                -detuning_value,
                detuning_value,
                detuning_value,
            ],
        )
    )

    distances = np.arange(4, 11, 1)
    batch = prog.assign(
        ramp_time=1.0, run_time=2.0, rabi_value=15.0, detuning_value=15.0
    ).batch_assign(atom_distance=distances)

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
