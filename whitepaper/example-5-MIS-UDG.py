from bloqade.ir.location import Square
import numpy as np

# durations for rabi and detuning
durations = [0.3, 1.6, 0.3]

mis_udg_program = (
    Square(15, 0.5)
    .apply_defect_density(0.5)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, [0.0, 15.0, 15.0, 0.0])
    .detuning.uniform.piecewise_linear(
        durations, [-30, -30, "final_detuning", "final_detuning"]
    )
)

# submit to HW
mis_udg_program.batch_assign(final_detuning=np.linspace(0, 80, 81)).mock(1000)

# submit to emulator would take too many resources
