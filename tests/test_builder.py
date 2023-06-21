# import bloqade.lattice as lattice

# geo = lattice.Square(3)
# prog = geo.rydberg.detuning
# for i in range(5):
#     prog = prog.location(i)
# prog.linear(start=1.0, stop=2.0, duration="x")
import bloqade.ir as ir
from bloqade import start, var
from bloqade.ir.location import Square, Chain
import numpy as np


def test_issue_107():
    waveform = (
        ir.Linear("initial_detuning", "initial_detuning", "up_time")
        .append(ir.Linear("initial_detuning", "final_detuning", "anneal_time"))
        .append(ir.Linear("final_detuning", "final_detuning", "up_time"))
    )

    prog1 = start.rydberg.detuning.uniform.apply(waveform)
    prog2 = start.rydberg.detuning.uniform.piecewise_linear(
        durations=["up_time", "anneal_time", "up_time"],
        values=[
            "initial_detuning",
            "initial_detuning",
            "final_detuning",
            "final_detuning",
        ],
    )

    assert prog1.sequence == prog2.sequence


def test_issue_150():
    prog = start.rydberg.detuning.uniform.linear(0, 1, 1).amplitude.uniform.linear(
        0, 2, 1
    )

    assert prog.sequence == ir.Sequence(
        {
            ir.rydberg: ir.Pulse(
                {
                    ir.rabi.amplitude: ir.Field({ir.Uniform: ir.Linear(0, 2, 1)}),
                    ir.detuning: ir.Field({ir.Uniform: ir.Linear(0, 1, 1)}),
                }
            )
        }
    )


prog = start
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


job = (
    Square(4, lattice_spacing="a")
    .apply_defect_density(0.1)
    .rydberg.detuning.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[-10, -10, "final_detuning", "final_detuning"]
    )
    .rabi.amplitude.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[0.0, 15.0, 15.0, 0.0]
    )
    .assign(final_detuning=20, a=4)
    .mock(100)
)
print(job)

job = (
    Square(4, lattice_spacing="a")
    .apply_defect_count(4)
    .rydberg.detuning.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[-10, -10, "final_detuning", "final_detuning"]
    )
    .rabi.amplitude.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[0.0, 15.0, 15.0, 0.0]
    )
    .assign(final_detuning=20, a=4)
    .mock(100)
)
print(job)


job = (
    start.add_position((0, 0))
    .add_position((6, 0))
    .add_position((3, "distance"))
    .rydberg.detuning.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[-10, -10, "final_detuning", "final_detuning"]
    )
    .rabi.amplitude.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[0.0, 15.0, 15.0, 0.0]
    )
    .parallelize(20.0)
    .assign(final_detuning=20, distance=4)
    .mock(100)
)
print(job)

job = (
    start.add_position((0, 0))
    .add_position((6, 0))
    .add_position((3, "distance"))
    .rydberg.detuning.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[-10, -10, "final_detuning", "final_detuning"]
    )
    .rabi.amplitude.uniform.piecewise_linear(
        durations=[0.1, 3.8, 0.1], values=[0.0, 15.0, 15.0, 0.0]
    )
    .parallelize(20.0)
    .assign(final_detuning=20, distance=4)
    .mock(100)
)

print(job)


def my_func(time, *, omega, phi=0, amplitude):
    return amplitude * np.cos(omega * time + phi)


durations = ir.cast([0.1, "run_time", 0.1])
total_duration = sum(durations)

job = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.fn(my_func, total_duration)
    .sample(0.05, "linear")
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations, [0, "rabi_max", "rabi_max", 0]
    )
    .assign(omega=15, amplitude=15, rabi_max=15)
    .batch_assign(run_time=np.linspace(0, 4.0, 101))
    .braket_local_simulator(1000)
)

print(job)


n_atoms = 11
atom_spacing = 6.1
run_time = var("run_time")
run_times = np.linspace(0.1, 4.0, 11)

quantum_scar_program = (
    Chain(11, lattice_spacing=atom_spacing)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        [0.3, 1.6, 0.3], [0.0, 15.7, 15.7, 0.0]
    )
    .piecewise_linear([0.2, 1.4, 0.2], [0, 15.7, 15.7, 0])
    .slice(stop=run_time - 0.06)
    .record("rabi_value")
    .linear("rabi_value", 0, 0.06)
    .detuning.uniform.piecewise_linear([0.3, 1.6, 0.3], [-18.8, -18.8, 16.3, 16.3])
    .piecewise_linear([0.2, 1.6], [16.3, 0.0, 0.0])
    .slice(stop=run_time)
    .batch_assign(run_time=run_times)
    .braket_local_simulator(10000)
)
