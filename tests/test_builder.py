# import bloqade.lattice as lattice

# geo = lattice.Square(3)
# prog = geo.rydberg.detuning
# for i in range(5):
#     prog = prog.location(i)
# prog.linear(start=1.0, stop=2.0, duration="x")
import bloqade.ir as ir
from bloqade.builder.start import ProgramStart


def test_issue_107():
    waveform = (
        ir.Linear("initial_detuning", "initial_detuning", "up_time")
        .append(ir.Linear("initial_detuning", "final_detuning", "anneal_time"))
        .append(ir.Linear("final_detuning", "final_detuning", "up_time"))
    )

    prog1 = ProgramStart().rydberg.detuning.uniform.apply(waveform)
    prog2 = ProgramStart().rydberg.detuning.uniform.piecewise_linear(
        durations=["up_time", "anneal_time", "up_time"],
        values=[
            "initial_detuning",
            "initial_detuning",
            "final_detuning",
            "final_detuning",
        ],
    )

    assert prog1.sequence == prog2.sequence


prog = ProgramStart()
prog = (
    prog.rydberg.detuning.location(1)
    .location(2)
    .linear(start=1.0, stop=2.0, duration="x")
    .poly(coeffs=[1, 2, 3], duration="x")
    .location(3)
    .location(4)
    .constant(value=1.0, duration="x")
    .rabi.amplitude.location(5)
    .location(6)
    .linear(start=1.0, stop=2.0, duration="x")
    .phase.location(7)
    .constant(value=1.0, duration="x")
    .apply(ir.Linear(1.0, 2.0, "x"))
    .hyperfine.detuning.location(8)
    .poly(coeffs=[1, 2, 3], duration="x")
)
print(prog)

for idx in range(5):
    prog = prog.location(idx).linear(start=1.0, stop=2.0, duration="x")

print(prog)
print(prog.sequence)
