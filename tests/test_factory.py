import pytest
from bloqade import (
    waveform,
    rydberg_h,
    piecewise_linear,
    piecewise_constant,
    constant,
    linear,
    var,
    cast,
    start,
    get_capabilities,
)
from bloqade.atom_arrangement import Chain
from bloqade.ir import (
    AnalogCircuit,
    Sequence,
    rydberg,
    Pulse,
    rabi,
    detuning,
    Field,
    Uniform,
)
from bloqade.ir.routine.base import Routine
from bloqade.ir.routine.params import Params
import numpy as np
from decimal import Decimal


def test_get_capabilities():
    capabilities = get_capabilities()

    assert capabilities.version == "0.6"
    assert capabilities.capabilities.task.number_shots_min == 1
    assert capabilities.capabilities.task.number_shots_max == 1000
    assert capabilities.capabilities.lattice.number_qubits_max == 256
    assert capabilities.capabilities.lattice.area.width == Decimal("75.0")
    assert capabilities.capabilities.lattice.area.height == Decimal("76.0")
    assert capabilities.capabilities.lattice.geometry.spacing_radial_min == Decimal(
        "4.0"
    )
    assert capabilities.capabilities.lattice.geometry.spacing_vertical_min == Decimal(
        "4.0"
    )
    assert capabilities.capabilities.lattice.geometry.position_resolution == Decimal(
        "0.1"
    )
    assert capabilities.capabilities.lattice.geometry.number_sites_max == 256
    assert capabilities.capabilities.rydberg.c6_coefficient == Decimal("5.42e6")
    assert capabilities.capabilities.rydberg.global_.rabi_frequency_min == Decimal(
        "0.0"
    )
    assert capabilities.capabilities.rydberg.global_.rabi_frequency_max == Decimal(
        "15.8"
    )
    assert (
        capabilities.capabilities.rydberg.global_.rabi_frequency_resolution
        == Decimal("4.0e-4")
    )
    assert (
        capabilities.capabilities.rydberg.global_.rabi_frequency_slew_rate_max
        == Decimal("250.0")
    )
    assert capabilities.capabilities.rydberg.global_.detuning_min == Decimal("-125.0")
    assert capabilities.capabilities.rydberg.global_.detuning_max == Decimal("125.0")
    assert capabilities.capabilities.rydberg.global_.detuning_resolution == Decimal(
        "2.0e-7"
    )
    assert capabilities.capabilities.rydberg.global_.detuning_slew_rate_max == Decimal(
        "2500.0"
    )
    assert capabilities.capabilities.rydberg.global_.phase_min == Decimal("-99.0")
    assert capabilities.capabilities.rydberg.global_.phase_max == Decimal("99.0")
    assert capabilities.capabilities.rydberg.global_.phase_resolution == Decimal(
        "5.0E-7"
    )
    assert capabilities.capabilities.rydberg.global_.time_min == Decimal("0.0")
    assert capabilities.capabilities.rydberg.global_.time_max == Decimal("4.0")
    assert capabilities.capabilities.rydberg.global_.time_resolution == Decimal("1e-3")
    assert capabilities.capabilities.rydberg.global_.time_delta_min == Decimal("5e-2")
    assert capabilities.capabilities.rydberg.local.detuning_min == Decimal("0.0")
    assert capabilities.capabilities.rydberg.local.detuning_max == Decimal("125.0")
    assert capabilities.capabilities.rydberg.local.detuning_slew_rate_max == Decimal(
        "1.2566e3"
    )
    assert capabilities.capabilities.rydberg.local.site_coefficient_min == Decimal(
        "0.0"
    )
    assert capabilities.capabilities.rydberg.local.site_coefficient_max == Decimal(
        "1.0"
    )
    assert (
        capabilities.capabilities.rydberg.local.number_local_detuning_sites
        == Decimal("200")
    )
    assert capabilities.capabilities.rydberg.local.spacing_radial_min == Decimal("5.0")
    assert capabilities.capabilities.rydberg.local.time_resolution == Decimal("1e-3")
    assert capabilities.capabilities.rydberg.local.time_delta_min == Decimal("5e-2")


def test_ir_piecewise_linear():
    A = piecewise_linear([0.1, 3.8, 0.2], [-10, -7, "a", "b"])

    ## Append type ir node
    assert len(A.waveforms) == 3
    assert A.waveforms[0].duration == cast(0.1)
    assert A.waveforms[0].start == cast(-10)
    assert A.waveforms[0].stop == cast(-7)

    assert A.waveforms[1].duration == cast(3.8)
    assert A.waveforms[1].start == cast(-7)
    assert A.waveforms[1].stop == cast("a")

    assert A.waveforms[2].duration == cast(0.2)
    assert A.waveforms[2].start == cast("a")
    assert A.waveforms[2].stop == cast("b")

    with pytest.raises(ValueError):
        piecewise_linear([0.1, 3.8, 0.2], [-10, -7, "a", "b", "c"])


def test_ir_const():
    A = constant(value=3.415, duration=0.55)

    ## Constant type ir node:
    assert A.value == cast(3.415)
    assert A.duration == cast(0.55)


def test_ir_linear():
    A = linear(start=0.5, stop=3.2, duration=0.76)

    ## Linear type ir node:
    assert A.start == cast(0.5)
    assert A.stop == cast(3.2)
    assert A.duration == cast(0.76)


def test_ir_piecewise_constant():
    A = piecewise_constant(durations=[0.1, 3.8, 0.2], values=[-10, "a", "b"])

    assert A.waveforms[0].duration == cast(0.1)
    assert A.waveforms[0].value == cast(-10)

    assert A.waveforms[1].duration == cast(3.8)
    assert A.waveforms[1].value == cast("a")

    assert A.waveforms[2].duration == cast(0.2)
    assert A.waveforms[2].value == cast("b")

    with pytest.raises(ValueError):
        piecewise_constant([0.1, 3.8, 0.2], [-10, -7, "a", "b"])


def test_rydberg_h():
    run_time = var("run_time")

    @waveform(run_time + 0.2)
    def delta(t, amp, omega):
        return np.sin(omega * t) * amp

    delta = delta.sample(0.05, "linear")
    ampl = piecewise_linear([0.1, run_time, 0.1], [0, 10, 10, 0])
    phase = piecewise_constant([2, 2], [0, np.pi])
    register = Chain(11, lattice_spacing=6.1)

    static_params = {"amp": 1.0}
    batch_params = [{"omega": omega} for omega in [1, 2, 4, 8]]
    args = ["run_time"]

    routine = rydberg_h(
        register,
        detuning=delta,
        amplitude=ampl,
        phase=phase,
        batch_params=batch_params,
        static_params=static_params,
        args=args,
    )

    detuning_field = Field({Uniform: delta})
    ampl_field = Field({Uniform: ampl})
    phase_field = Field({Uniform: phase})

    pulse = Pulse(
        {detuning: detuning_field, rabi.amplitude: ampl_field, rabi.phase: phase_field}
    )
    sequence = Sequence({rydberg: pulse})

    source = (
        register.rydberg.detuning.uniform.apply(delta)
        .amplitude.uniform.apply(ampl)
        .phase.uniform.apply(phase)
        .assign(**static_params)
        .batch_assign(batch_params)
        .args(args)
    )

    circuit = AnalogCircuit(register, sequence)
    params = Params(static_params, batch_params, args)
    expected_routine = Routine(source, circuit, params)

    # ignore because no equality implemented
    # assert routine.source == expected_routine.source
    assert routine.circuit == expected_routine.circuit
    assert routine.params == expected_routine.params


def test_rydberg_h_2():
    run_time = var("run_time")

    @waveform(run_time + 0.2)
    def delta(t, amp, omega):
        return np.sin(omega * t) * amp

    delta = delta.sample(0.05, "linear")
    ampl = piecewise_linear([0.1, run_time, 0.1], [0, 10, 10, 0])
    phase = piecewise_constant([2, 2], [0, np.pi])
    register = start.add_position((0, 0))

    prog = rydberg_h(
        (0, 0), detuning=delta, amplitude=ampl, phase=phase, batch_params={}
    )

    detuning_field = Field({Uniform: delta})
    ampl_field = Field({Uniform: ampl})
    phase_field = Field({Uniform: phase})

    pulse = Pulse(
        {detuning: detuning_field, rabi.amplitude: ampl_field, rabi.phase: phase_field}
    )
    sequence = Sequence({rydberg: pulse})

    print(prog.parse_circuit())
    print(AnalogCircuit(register, sequence))

    assert prog.parse_circuit() == AnalogCircuit(register, sequence)
