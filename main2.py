from bloqade import start, piecewise_linear

# from bloqade.builder2.compile import PulseCompiler
from bloqade.codegen.common.static_assign import StaticAssignWaveform
import bloqade.ir as ir


prog = (
    start.add_position((1, 1))
    # .hyperfine.rabi.amplitude.location(1)
    # .rydberg.detuning.location(0)
    # .rydberg.rabi.phase
    .rydberg.detuning.uniform.constant(value=2.0, duration=1.0)
    .rydberg.rabi.amplitude.location(0)
    .location(1)
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
    .assign()
    .flatten(["a"])
    .quera.aquila()
    # .assign().batch_assign().quera.aquila(10)
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


# sequence = PulseCompiler(prog).compile()

# print(repr(sequence))


wf = piecewise_linear(["t", "T", "t"], ["a", "b", "a", "d"])


new_wf = StaticAssignWaveform(dict(a=3.123091023)).emit(wf)

print(repr(new_wf))


scaled_locations = ir.ScaledLocations(
    {ir.Location(1): ir.cast(1.0), ir.Location(0): ir.cast(2.0)}
)
print(scaled_locations)
