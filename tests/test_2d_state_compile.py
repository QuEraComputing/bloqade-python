from bloqade.atom_arrangement import Square


def test_2d_state_compile():
    # Have atoms separated by 5.9 micrometers
    L = 3
    lattice_spacing = 5.9

    rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
    rabi_detuning_values = [-16.33, -16.33, "delta_end", "delta_end"]
    durations = [0.8, "sweep_time", 0.8]

    prog = (
        Square(L, lattice_spacing=lattice_spacing)
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations, rabi_amplitude_values
        )
        .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
    )

    batch = prog.assign(delta_end=42.66, sweep_time=2.4)

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
