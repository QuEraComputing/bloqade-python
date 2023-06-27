from bloqade.ir.location import Square

# from bokeh.plotting import figure, show

n_atoms = 11

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 42.66, 42.66]
durations = [0.8, 2.4, 0.8]

ordered_state_2D_prog = (
    Square(n_atoms, 5.9)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

ordered_state_2D_job = ordered_state_2D_prog.braket(100).submit().report()
