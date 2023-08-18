# import bloqade.lattice as lattice

# geo = lattice.Square(3)
# prog = geo.rydberg.detuning
# for i in range(5):
#     prog = prog.location(i)
# prog.linear(start=1.0, stop=2.0, duration="x")
# import pytest
import bloqade.ir as ir
from bloqade.builder import location, waveform
from bloqade.ir import rydberg, detuning, hyperfine, rabi
from bloqade import start, cast

# from bloqade.ir.location import Square, Chain
# import numpy as np
import pytest


def test_piecewise_const():
    prog = start.rydberg.detuning.uniform.piecewise_constant(
        durations=[0.1, 3.1, 0.05], values=[4, 4, 7.5]
    )

    ## inspect ir
    node1 = prog
    ir1 = node1._waveform
    assert ir1.value == cast(7.5)
    assert ir1.duration == cast(0.05)

    node2 = node1.__parent__
    ir2 = node2._waveform
    assert ir2.value == cast(4)
    assert ir2.duration == cast(3.1)

    node3 = node2.__parent__
    ir3 = node3._waveform
    assert ir3.value == cast(4)
    assert ir3.duration == cast(0.1)


def test_registers():
    waveform = (
        ir.Linear("initial_detuning", "initial_detuning", "up_time")
        .append(ir.Linear("initial_detuning", "final_detuning", "anneal_time"))
        .append(ir.Linear("final_detuning", "final_detuning", "up_time"))
    )
    prog1 = start.rydberg.detuning.uniform.apply(waveform)
    reg = prog1.compile_register()

    assert reg.n_atoms == 0
    assert reg.n_dims is None


def test_scale():
    prog = start
    prog = (
        prog.rydberg.detuning.location(1)
        .scale(1.2)
        .piecewise_linear([0.1, 3.8, 0.1], [-10, -10, "a", "b"])
    )

    ## let Emit build ast
    seq = prog.compile_sequence()

    print(type(list(seq.value.keys())[0]))
    Loc1 = list(seq.value[rydberg].value[detuning].value.keys())[0]

    assert type(Loc1) == ir.ScaledLocations
    assert Loc1.value[ir.Location(1)] == cast(1.2)


def test_scale_location():
    prog = start.rydberg.detuning.location(1).scale(1.2).location(2).scale(3.3)

    assert prog._scale == cast(3.3)
    assert type(prog.__parent__) == location.Location
    assert prog.__parent__.__parent__._scale == cast(1.2)


def test_build_ast_Scale():
    prog = (
        start.rydberg.detuning.location(1)
        .scale(1.2)
        .location(2)
        .scale(3.3)
        .piecewise_constant(durations=[0.1], values=[1])
    )

    # compile ast:
    tmp = prog.compile_sequence()

    locs = list(tmp.value[rydberg].value[detuning].value.keys())[0]
    wvfm = tmp.value[rydberg].value[detuning].value[locs]

    assert locs == ir.ScaledLocations(
        {ir.Location(2): cast(3.3), ir.Location(1): cast(1.2)}
    )
    assert wvfm == ir.Constant(value=cast(1), duration=cast(0.1))


def test_spatial_var():
    prog = start.rydberg.detuning.var("a")

    assert prog._name == "a"

    prog = prog.piecewise_constant([0.1], [30])

    # test build ast:
    seq = prog.sequence

    assert seq.value[rydberg].value[detuning].value[
        ir.RunTimeVector("a")
    ] == ir.Constant(value=30, duration=0.1)


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

    assert prog1.compile_sequence() == prog2.compile_sequence()


def test_issue_150():
    prog = start.rydberg.detuning.uniform.linear(0, 1, 1).amplitude.uniform.linear(
        0, 2, 1
    )

    assert prog.compile_sequence() == ir.Sequence(
        {
            ir.rydberg: ir.Pulse(
                {
                    ir.rabi.amplitude: ir.Field({ir.Uniform: ir.Linear(0, 2, 1)}),
                    ir.detuning: ir.Field({ir.Uniform: ir.Linear(0, 1, 1)}),
                }
            )
        }
    )


def test_303_replicate_channel_should_add():
    prog = (
        start.rydberg.detuning.uniform.linear(0, 1, 1)
        .rabi.amplitude.uniform.linear(1, 2, 1)
        .detuning.uniform.linear(0, 2, 3)
    )

    assert prog.compile_sequence() == ir.Sequence(
        {
            ir.rydberg: ir.Pulse(
                {
                    ir.rabi.amplitude: ir.Field({ir.Uniform: ir.Linear(1, 2, 1)}),
                    ir.detuning: ir.Field(
                        {ir.Uniform: ir.Linear(0, 2, 3) + ir.Linear(0, 1, 1)}
                    ),
                }
            )
        }
    )

    prog1 = (
        start.rydberg.detuning.uniform.linear(0, 1, 1)
        .rabi.amplitude.uniform.linear(1, 2, 1)
        .rydberg.detuning.uniform.linear(0, 2, 3)
    )

    assert prog1.compile_sequence() == prog.compile_sequence()


def test_record():
    prog = start
    prog = (
        prog.rydberg.detuning.location(1)
        .piecewise_constant([0.1], [30])
        .record("detuning")
    )

    assert type(prog) == waveform.Record

    seq = prog.compile_sequence()
    assert seq.value[rydberg].value[detuning].value[
        ir.ScaledLocations({ir.Location(1): cast(1)})
    ] == ir.Record(waveform=ir.Constant(value=30, duration=0.1), var=cast("detuning"))


def test_hyperfine_phase():
    prog = start.hyperfine.rabi.phase.location(1).piecewise_constant([0.1], [30])

    seq = prog.compile_sequence()

    assert seq.value[hyperfine].value[rabi.phase].value[
        ir.ScaledLocations({ir.Location(1): cast(1)})
    ] == ir.Constant(value=30, duration=0.1)


def test_hyperfine_amplitude():
    prog = start.hyperfine.rabi.amplitude.location(1).piecewise_constant([0.1], [30])

    seq = prog.compile_sequence()

    assert seq.value[hyperfine].value[rabi.amplitude].value[
        ir.ScaledLocations({ir.Location(1): cast(1)})
    ] == ir.Constant(value=30, duration=0.1)


def test_fatal_apply():
    prog = start.hyperfine.rabi.amplitude.location(1).piecewise_constant([0.1], [30])

    st = start
    seq = prog.compile_sequence()
    st.__sequence__ = seq

    with pytest.raises(NotImplementedError):
        st.apply(seq)


def test_piecewise_constant_mismatch():
    with pytest.raises(ValueError):
        start.hyperfine.rabi.amplitude.location(1).piecewise_constant([0.1, 0.5], [30])


def test_piecewise_linear_mismatch():
    with pytest.raises(ValueError):
        start.hyperfine.rabi.amplitude.location(1).piecewise_linear(
            durations=[0.1, 0.5], values=[30, 20]
        )


"""
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


sequence = (
    start.rydberg.detuning.uniform.fn(my_func, total_duration)
    .sample(0.05, "linear")
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations, [0, "rabi_max", "rabi_max", 0]
    )
    .sequence
)

builder = start
for site in range(11):
    builder = builder.add_position((6 * site, 0))
    job = (
        builder.apply(sequence)
        .assign(omega=15, amplitude=15, rabi_max=15)
        .batch_assign(run_time=np.linspace(0, 4.0, 101))
        .braket_local_simulator(1000)
    )
    print(job)
"""
