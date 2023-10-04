# from bloqade import start
from bloqade.ir import location, cast, Interpolation
from bloqade.ir import Constant, Linear, Poly, PythonFn, Sample
import pytest
import json
import numpy as np


"""
import bloqade.ir.location as location
from bloqade.codegen.hardware.quera import SchemaCodeGen
from bloqade.submission.base import get_capabilities

bloqade_program = (
    location.Square(1)
    .rydberg.rabi.phase.uniform.piecewise_constant(
        durations=[0.5, 0.5], values=[0, 1]
    )
    .piecewise_constant(
        durations=[0.3] ,values = [0.2]
    ).program
)

capabilities = get_capabilities()
schema = SchemaCodeGen({},capabilities=capabilities).emit(10, bloqade_program)

print(schema.effective_hamiltonian.rydberg.rabi_frequency_phase.global_.times)
"""


def fc(x):
    return float(x)


def fvec(v):
    return list(map(fc, v))


def test_integration_jump_err():
    ## jump at the end of linear -- constant
    with pytest.raises(ValueError):
        (
            location.Square(6)
            .rydberg.detuning.uniform.apply(
                Constant("initial_detuning", "up_time")
                .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
                .append(0.5 * Constant("final_detuning", "up_time"))
            )
            .assign(
                initial_detuning=-10,
                up_time=0.1,
                final_detuning=15,
                anneal_time=10,
            )
            .quera.mock()
            ._compile(10)
        )


def test_integration_scale():
    seq = Linear(start=0.0, stop=1.0, duration=0.5).append(
        2 * Constant(0.5, duration=0.5)
    )
    job = (
        location.Square(1)
        .rydberg.detuning.uniform.apply(seq)
        .quera.mock()
        ._compile(shots=10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(fvec(detune_ir["global"]["values"]) == np.array([0, 1, 1]) * 1e6)


def test_integration_neg():
    seq = Linear(start=0.0, stop=-0.5, duration=0.5).append(
        -Constant(0.5, duration=0.5)
    )
    job = (
        location.Square(1)
        .rydberg.detuning.uniform.apply(seq)
        .quera.mock()
        ._compile(shots=10)
    )

    panel = json.loads(job.json())
    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(fvec(detune_ir["global"]["values"]) == np.array([0, -0.5, -0.5]) * 1e6)


def test_integration_poly_order_err():
    ## poly
    with pytest.raises(ValueError):
        seq = Poly(coeffs=[1, 2, 3], duration=0.5).append(-Constant(0.5, duration=0.5))
        (
            location.Square(1)
            .rydberg.detuning.uniform.apply(seq)
            .quera.mock()
            ._compile(shots=10)
        )


def test_integration_poly_const():
    ## constant
    seq = Poly(coeffs=[1], duration=0.5).append(Constant(1, duration=0.5))
    job = (
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(12)
    )

    panel = json.loads(job.json())
    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 12
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(fvec(detune_ir["global"]["values"]) == np.array([1, 1, 1]) * 1e6)


def test_integration_poly_linear():
    ## linear
    seq = Poly(coeffs=[1, 2], duration=0.5).append(Constant(2, duration=0.5))
    job = (
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(10)
    )

    panel = json.loads(job.json())
    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(fvec(detune_ir["global"]["values"]) == np.array([1, 2, 2]) * 1e6)


def test_integration_linear_sampl_const_err():
    def my_cos(time):
        return np.cos(time)

    assert my_cos(1) == np.cos(1)

    wv = PythonFn.create(my_cos, duration=1.0)
    dt = cast(0.1)

    wf = Sample(wv, Interpolation.Constant, dt)
    ## phase can only have piecewise constant.
    with pytest.raises(ValueError):
        location.Square(1).rydberg.detuning.uniform.apply(wf).quera.mock()._compile(10)


def test_integration_slice_linear_const():
    seq = Linear(start=0.0, stop=1.0, duration=1.0)[0:0.5].append(
        Constant(0.5, duration=0.5)
    )
    job = (
        location.Square(1)
        .rydberg.detuning.uniform.apply(seq)
        .quera.mock()
        ._compile(shots=10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(fvec(detune_ir["global"]["values"]) == np.array([0, 0.5, 0.5]) * 1e6)


def test_integration_slice_linear_no_stop():
    seq = Linear(start=0.0, stop=1.0, duration=1.0)[0:]
    job = (
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 1.0]) * 1e-6)
    assert all(fvec(detune_ir["global"]["values"]) == np.array([0, 1.0]) * 1e6)


def test_integration_slice_linear_no_start():
    seq = Linear(start=0.0, stop=1.0, duration=1.0)[:1.0]
    job = (
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]
    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 1.0]) * 1e-6)
    assert all(fvec(detune_ir["global"]["values"]) == np.array([0, 1.0]) * 1e6)


def test_integration_slice_linear_error_neg_start():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[-0.1:1.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(10)


def test_integration_slice_linear_error_exceed_stop():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[:4.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(10)


def test_integration_slice_linear_error_revese():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[0.5:0.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(10)


def test_integration_slice_linear_error_same_vals_nofield():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[0.0:0.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).quera.mock()._compile(10)


def test_integration_phase():
    batch = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.piecewise_constant(
            durations=[0.5, 0.5], values=[0, 1]
        )
        .record("a")
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(batch.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([0, 1.0, 1.0]))


def test_intergration_phase_nonconst_err():
    with pytest.raises(ValueError):
        (
            location.Square(1)
            .rydberg.rabi.phase.uniform.piecewise_linear(
                durations=[0.5, 0.5], values=[0, 1, 2]
            )
            .quera.mock()
            ._compile(10)
        )

    seq = Poly(coeffs=[1, 2], duration=0.5)
    with pytest.raises(ValueError):
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).quera.mock()._compile(
            10
        )


def test_integration_phase_linear():
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.linear(start=1, stop=1, duration=1)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 1.0]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([1.0, 1.0]))


def test_integration_phase_polyconst():
    seq = Poly(coeffs=[1], duration=0.5)
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.apply(seq)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([1.0, 1.0]))


def test_integration_phase_slice():
    ##[Further investigate!]
    seq = Poly(coeffs=[1], duration=1.0)[0:0.5]
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.apply(seq)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([1.0, 1.0]))


def test_integration_phase_scale():
    seq = 3.0 * Constant(value=1.0, duration=1.0)
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.apply(seq)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 1.0]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([3.0, 3.0]))


def test_integration_phase_neg():
    seq = -Constant(value=1.0, duration=1.0)
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.apply(seq)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 1.0]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([-1.0, -1.0]))


def test_integration_phase_slice_no_start():
    seq = Poly(coeffs=[1], duration=1.0)[:0.5]
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.apply(seq)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([1.0, 1.0]))


def test_integration_phase_slice_no_stop():
    ##[Further investigate!]
    seq = Poly(coeffs=[1], duration=0.5)[0:]
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.apply(seq)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([1.0, 1.0]))


def test_integration_phase_slice_same_start_stop():
    ##[Further investigate!]
    seq = Poly(coeffs=[1], duration=0.5)[0:0.5]
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.apply(seq)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([1.0, 1.0]))


def test_integration_phase_slice_error_neg_start():
    with pytest.raises(ValueError):
        seq = Poly(coeffs=[1], duration=1.0)[-0.1:0.5]
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).quera.mock()._compile(
            10
        )


def test_integration_phase_slice_error_exceed_stop():
    with pytest.raises(ValueError):
        seq = Poly(coeffs=[1], duration=1.0)[0:2.0]
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).quera.mock()._compile(
            10
        )


def test_integration_phase_slice_error_reverse():
    with pytest.raises(ValueError):
        seq = Poly(coeffs=[1], duration=1.0)[2.0:0.0]
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).quera.mock()._compile(
            10
        )


def test_integration_phase_sampl_linear_err():
    def my_cos(time):
        return np.cos(time)

    assert my_cos(1) == np.cos(1)

    wv = PythonFn.create(my_cos, duration=1.0)
    dt = cast(0.1)

    wf = Sample(wv, Interpolation.Linear, dt)
    ## phase can only have piecewise constant.
    with pytest.raises(ValueError):
        location.Square(1).rydberg.rabi.phase.uniform.apply(wf).quera.mock()._compile(
            10
        )


def test_integration_batchassign_assign():
    ## jump at the end of linear -- constant
    with pytest.raises(ValueError):
        (
            location.Square(6)
            .rydberg.detuning.uniform.apply(Constant("initial_detuning", "time"))
            .batch_assign(initial_detuning=[1, 2, 3, 4], time=[2, 4, 5])
            .quera.mock()
            ._compile(10)
        )

    ## jump at the end of linear -- constant

    batch = (
        location.Square(6)
        .rydberg.detuning.uniform.apply(Constant("initial_detuning", "time"))
        .batch_assign(initial_detuning=[1, 2, 3, 4], time=[2, 4, 5, 0.6])
        .quera.mock()
        ._compile(10)
    )

    assert len(batch.tasks) == 4


def test_integration_record():
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.piecewise_constant(
            durations=[0.5, 0.5], values=[0, 1]
        )
        .record("a")
        .piecewise_constant(durations=[0.3], values=["a"])
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5, 1.0, 1.3]) * 1e-6)
    assert all(fvec(phase_ir["global"]["values"]) == np.array([0, 1.0, 1.0, 1.0]))


pytest.mark.skip(reason="fixing now")


def test_integration_fn_phase():
    def my_cos(time):
        return np.cos(time)

    assert my_cos(1) == np.cos(1)

    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.fn(my_cos, duration=1.0)
        .sample(dt=0.5)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(fvec(phase_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(
        fvec(phase_ir["global"]["values"]) == np.array([1.0, 0.8775825, 0.8775825])
    )


pytest.mark.skip(reason="fixing now")


def test_integration_fn_detune():
    def my_cos(time):
        return np.cos(time)

    assert my_cos(1) == np.cos(1)

    job = (
        location.Square(1)
        .rydberg.detuning.uniform.fn(my_cos, duration=1.0)
        .sample(dt=0.5)
        .quera.mock()
        ._compile(10)
    )

    panel = json.loads(job.json())

    print(panel)

    task_data = panel["bloqade.task.batch.RemoteBatch"]["tasks"][0][1]

    ir = task_data["bloqade.task.quera.QuEraTask"]["task_ir"]

    assert ir["nshots"] == 10
    assert fvec(ir["lattice"]["sites"][0]) == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(fvec(detune_ir["global"]["times"]) == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(
        fvec(detune_ir["global"]["values"]) == np.array([1000000, 877582.6, 540302.4])
    )
