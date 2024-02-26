from bloqade.atom_arrangement import Square
import numpy as np


def test_mis_compile():
    rng = np.random.default_rng(1234)

    durations = [0.3, 1.6, 0.3]

    mis_udg_program = (
        Square(15, lattice_spacing=5.0)
        .apply_defect_density(0.3, rng=rng)
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations, [0.0, 15.0, 15.0, 0.0]
        )
        .detuning.uniform.piecewise_linear(
            durations, [-30, -30, "final_detuning", "final_detuning"]
        )
    )

    mis_udg_job = mis_udg_program.batch_assign(final_detuning=np.linspace(0, 80, 41))

    # skip emulation targets considering not feasible to emulate
    # bloqade_emu_target = mis_udg_job.bloqade.python()
    # braket_emu_target = mis_udg_job.braket.local_emulator()
    quera_aquila_target = mis_udg_job.quera.aquila()
    braket_aquila_target = mis_udg_job.braket.aquila()

    targets = [quera_aquila_target, braket_aquila_target]

    for target in targets:
        target._compile(10)
