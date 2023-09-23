# import bloqade.lattice as lattice

# geo = lattice.Square(3)
# prog = geo.rydberg.detuning
# for i in range(5):
#     prog = prog.location(i)
# prog.linear(start=1.0, stop=2.0, duration="x")
# import pytest
import bloqade.ir as ir
from bloqade.builder import spatial
from bloqade.builder import waveform

# import bloqade.builder.backend as builder_backend
import bloqade.ir.routine.quera as quera
import bloqade.ir.routine.braket as braket

from bloqade.ir.control.waveform import instruction
from bloqade.ir import rydberg, detuning, hyperfine, rabi
from bloqade import start, cast, var

# from bloqade.ir.location import Square, Chain
import numpy as np
import pytest


def test_assign_checks():
    t = var("t")

    t_2 = var("T").max(t)
    t_1 = var("T").min(t)

    delta = var("delta") / (2 * np.pi)
    omega_max = var("omega_max") * 2 * np.pi

    @instruction(t_2)
    def detuning(t, u):
        return np.abs(t) * u

    with pytest.raises(ValueError):
        (
            start.add_position(("x", "y"))
            .rydberg.rabi.amplitude.var("mask")
            .piecewise_linear([0.1, t - 0.2, 0.1], [0, omega_max, omega_max, 0])
            .slice(t_1, t_2)
            .uniform.poly([1, 2, 3, 4], t_1)
            .detuning.uniform.constant(10, t_2)
            .uniform.linear(0, delta, t_1)
            .phase.uniform.apply(-(2 * detuning))
            .assign(c=10)
        )

    with pytest.raises(ValueError):
        (
            start.add_position(("x", "y"))
            .rydberg.rabi.amplitude.var("mask")
            .piecewise_linear([0.1, t - 0.2, 0.1], [0, omega_max, omega_max, 0])
            .slice(t_1, t_2)
            .uniform.poly([1, 2, 3, 4], t_1)
            .detuning.uniform.constant(10, t_2)
            .uniform.linear(0, delta, t_1)
            .phase.uniform.apply(-(2 * detuning))
            .batch_assign(c=[10])
        )


def test_add_position_dispatch():
    position = np.array([[1, 2], [3, 4]])
    position_list = list(map(tuple, position.tolist()))

    a = start.add_position(position)
    b = start.add_position(position_list)
    c = start.add_position(position_list[0]).add_position(position_list[1])

    assert a.location_list == b.location_list
    assert a.location_list == c.location_list

    with pytest.raises(AssertionError):
        start.add_position(position_list, [True])


def test_piecewise_const():
    prog = start.rydberg.detuning.uniform.piecewise_constant(
        durations=[0.1, 3.1, 0.05], values=[4, 4, 7.5]
    )

    ## inspect ir
    node1 = prog.__bloqade_ir__()
    ir1 = node1.waveforms[2]
    assert ir1.value == cast(7.5)
    assert ir1.duration == cast(0.05)

    ir2 = node1.waveforms[1]
    assert ir2.value == cast(4)
    assert ir2.duration == cast(3.1)

    ir3 = node1.waveforms[0]
    assert ir3.value == cast(4)
    assert ir3.duration == cast(0.1)


def test_registers():
    waveform = (
        ir.Linear("initial_detuning", "initial_detuning", "up_time")
        .append(ir.Linear("initial_detuning", "final_detuning", "anneal_time"))
        .append(ir.Linear("final_detuning", "final_detuning", "up_time"))
    )
    prog1 = start.rydberg.detuning.uniform.apply(waveform)
    reg = prog1.parse_register()

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
    seq = prog.parse_sequence()

    # print(type(list(seq.pulses.keys())[0]))
    Loc1 = list(seq.pulses[rydberg].fields[detuning].value.keys())[0]

    assert type(Loc1) == ir.ScaledLocations
    assert Loc1.value[ir.Location(1)] == cast(1.2)


def test_scale_location():
    prog = start.rydberg.detuning.location(1).scale(1.2).location(2).scale(3.3)

    assert prog._value == 3.3
    assert type(prog.__parent__) == spatial.Location
    assert prog.__parent__.__parent__._value == 1.2


def test_build_ast_Scale():
    prog = (
        start.rydberg.detuning.location(1)
        .scale(1.2)
        .location(2)
        .scale(3.3)
        .piecewise_constant(durations=[0.1], values=[1])
    )

    # compile ast:
    tmp = prog.parse_sequence()

    locs = list(tmp.pulses[rydberg].fields[detuning].value.keys())[0]
    wvfm = tmp.pulses[rydberg].fields[detuning].value[locs]

    assert locs == ir.ScaledLocations(
        {ir.Location(2): cast(3.3), ir.Location(1): cast(1.2)}
    )
    assert wvfm == ir.Constant(value=cast(1), duration=cast(0.1))


def test_spatial_var():
    prog = start.rydberg.detuning.var("a")

    assert prog._name == "a"

    prog = prog.piecewise_constant([0.1], [30])

    # test build ast:
    seq = prog.parse_sequence()

    assert seq.pulses[rydberg].fields[detuning].value[
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

    assert prog1.parse_sequence() == prog2.parse_sequence()


def test_issue_150():
    prog = start.rydberg.detuning.uniform.linear(0, 1, 1).amplitude.uniform.linear(
        0, 2, 1
    )

    assert prog.parse_sequence() == ir.Sequence(
        {
            ir.rydberg: ir.Pulse(
                {
                    ir.detuning: ir.Field({ir.Uniform: ir.Linear(0, 1, 1)}),
                    ir.rabi.amplitude: ir.Field({ir.Uniform: ir.Linear(0, 2, 1)}),
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

    assert prog.parse_sequence() == ir.Sequence(
        {
            ir.rydberg: ir.Pulse(
                {
                    ir.detuning: ir.Field(
                        {ir.Uniform: ir.Linear(0, 1, 1) + ir.Linear(0, 2, 3)}
                    ),
                    ir.rabi.amplitude: ir.Field({ir.Uniform: ir.Linear(1, 2, 1)}),
                }
            )
        }
    )

    prog1 = (
        start.rydberg.detuning.uniform.linear(0, 1, 1)
        .rabi.amplitude.uniform.linear(1, 2, 1)
        .rydberg.detuning.uniform.linear(0, 2, 3)
    )

    assert prog1.parse_sequence() == prog.parse_sequence()


def test_record():
    prog = start
    prog = (
        prog.rydberg.detuning.location(1)
        .piecewise_constant([0.1], [30])
        .record("detuning")
    )

    assert type(prog) == waveform.Record

    seq = prog.parse_sequence()
    assert seq.pulses[rydberg].fields[detuning].value[
        ir.ScaledLocations({ir.Location(1): cast(1)})
    ] == ir.Record(waveform=ir.Constant(value=30, duration=0.1), var=cast("detuning"))


def test_hyperfine_phase():
    prog = start.hyperfine.rabi.phase.location(1).piecewise_constant([0.1], [30])

    seq = prog.parse_sequence()

    assert seq.pulses[hyperfine].fields[rabi.phase].value[
        ir.ScaledLocations({ir.Location(1): cast(1)})
    ] == ir.Constant(value=30, duration=0.1)


def test_hyperfine_amplitude():
    prog = start.hyperfine.rabi.amplitude.location(1).piecewise_constant([0.1], [30])

    seq = prog.parse_sequence()

    assert seq.pulses[hyperfine].fields[rabi.amplitude].value[
        ir.ScaledLocations({ir.Location(1): cast(1)})
    ] == ir.Constant(value=30, duration=0.1)


def test_piecewise_constant_mismatch():
    with pytest.raises(AssertionError):
        start.hyperfine.rabi.amplitude.location(1).piecewise_constant([0.1, 0.5], [30])


def test_piecewise_linear_mismatch():
    with pytest.raises(AssertionError):
        start.hyperfine.rabi.amplitude.location(1).piecewise_linear(
            durations=[0.1, 0.5], values=[30, 20]
        )


def test_backend_route():
    prog = start.rydberg.detuning.uniform.constant(4, 4)

    assert isinstance(prog.device("quera.aquila"), quera.QuEraHardwareRoutine)
    assert isinstance(prog.device("braket.aquila"), braket.BraketHardwareRoutine)
    assert isinstance(
        prog.device("braket.local_emulator"), braket.BraketLocalEmulatorRoutine
    )
    with pytest.raises(ValueError):
        prog.device("foo")


def test_assign_error():
    import numpy as np

    with pytest.raises(TypeError):
        start.rydberg.detuning.uniform.constant("c", "t").assign(c=np, t=10)

    with pytest.raises(TypeError):
        start.rydberg.detuning.uniform.constant("c", "t").batch_assign(
            c=[1, 2, np], t=[10]
        )

    with pytest.raises(TypeError):
        (
            start.add_position((0, 0))
            .rydberg.rabi.amplitude.uniform.piecewise_linear(
                [0.2, "rabi_dur_scanned", 0.2], [0.0, 10, 10, 0.0]
            )
            .batch_assign(rabi_dur_scanned=1.0)
        )

    with pytest.raises(TypeError):
        (
            start.add_position((0, 0))
            .rydberg.rabi.amplitude.uniform.piecewise_linear(
                [0.2, "rabi_dur_scanned", 0.2], [0.0, 10, 10, 0.0]
            )
            .assign(rabi_dur_scanned=[1.0])
        )

    with pytest.raises(TypeError):
        (
            start.add_position((0, 0))
            .rydberg.rabi.amplitude.uniform.piecewise_linear(
                [0.2, "rabi_dur_scanned", 0.2], [0.0, 10, 10, 0.0]
            )
            .amplitude.var("rabi_mask")
            .piecewise_linear([0.2, "rabi_dur_scanned", 0.2], [0.0, 10, 10, 0.0])
            .assign(rabi_mask=0.0)
            .batch_assign(rabi_dur_scanned=[1.0])
        )


def test_flatten_dupicate_error():
    with pytest.raises(ValueError):
        (
            start.add_position((0, 0))
            .rydberg.rabi.amplitude.uniform.constant("a", 1)
            .detuning.var("vec")
            .constant(1, 1)
            .assign(vec=[1])
            .args(["a", "a"])
            .braket.local_emulator()
            .run(1)
        )


def test_flatten_vector_error():
    with pytest.raises(ValueError):
        (
            start.add_position((0, 0))
            .rydberg.rabi.amplitude.uniform.constant(1, 1)
            .detuning.var("a")
            .constant(1, 1)
            .args(["a"])
            .braket.local_emulator()
            .run(1)
        )


def test_apply_sequence():
    sequence = start.rydberg.detuning.uniform.constant(1, 1).parse_sequence()

    start.add_position((0, 0)).apply(sequence).braket.local_emulator().run(1)


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
