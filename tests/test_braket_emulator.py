# import pytest
import pytest
from bloqade import start
from bloqade.serialize import loads, dumps

# import numpy as np


# @pytest.mark.skip(reason="not a good unit test, skip for now")
def test_braket_simulator_getbitstring():
    program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=[0.05, 1, 0.05], values=[0.0, 15.8, 15.8, 0.0]
        )
        .detuning.uniform.piecewise_linear(durations=[1.1], values=[0.0, 0.0])
    )
    print(program.parse().circuit.sequence)
    output = program.braket.local_emulator().run(shots=10).report()

    assert len(output.bitstrings()[0].flatten()) == 10


def test_serialize_braket_simulator_batch():
    program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=[0.05, 1, 0.05], values=[0.0, 15.8, 15.8, 0.0]
        )
        .detuning.uniform.piecewise_linear(durations=[1.1], values=[0.0, 0.0])
    )

    output = program.braket.local_emulator().run(shots=10)

    output_str = dumps(output)
    assert isinstance(loads(output_str), type(output))
    assert loads(output_str).tasks == output.tasks
    assert loads(output_str).name == output.name


def test_error():
    program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=[0.05, 1, 0.05], values=[0.0, 15.8, 15.8, 0.0]
        )
        .detuning.uniform.piecewise_linear(durations=[1.1], values=[0.0, 0.0])
    )

    output = program.braket.local_emulator()._compile(10)

    with pytest.raises(ValueError):
        output.tasks[0].result()

    output_str = dumps(output)
    assert isinstance(loads(output_str), type(output))
    assert loads(output_str).tasks == output.tasks
    assert loads(output_str).name == output.name


def test_assign_dur_zero_wf():
    (
        start.add_position([(0, 0), (0, 6)])
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "dur", 0.1], [0, 15, 15, 0]
        )
        .assign(dur=0)
        .braket.local_emulator()
        .run(shots=10)
    )


def test_assign_dur_zero_pulse():
    from bloqade.ir.control.sequence import rydberg, Sequence
    from bloqade.ir.routine.base import Routine
    from bloqade.ir.routine.params import Params
    from bloqade.ir.analog_circuit import AnalogCircuit

    atom_arrangement = start.add_position([(0, 0), (0, 6)])

    seq_seg_1 = start.rydberg.detuning.uniform.linear(0, 15, 0.1).parse_sequence()
    seq_seg_2 = start.rydberg.detuning.uniform.linear(15, 15, "dur").parse_sequence()
    seq_seg_3 = start.rydberg.detuning.uniform.linear(15, 0, 0.1).parse_sequence()

    pulse_seq_1 = seq_seg_1.pulses[rydberg]
    pulse_seq_2 = seq_seg_2.pulses[rydberg]
    pulse_seq_3 = seq_seg_3.pulses[rydberg]

    pulse = pulse_seq_1.append(pulse_seq_2).append(pulse_seq_3)
    sequence = Sequence(pulses={rydberg: pulse})
    circuit = AnalogCircuit(atom_arrangement=atom_arrangement, sequence=sequence)

    params = Params(2, {"dur": 0}, [], [])
    routine = Routine(source=None, circuit=circuit, params=params)
    routine.braket.local_emulator().run(shots=10)


def test_assign_dur_zero_sequence():
    from bloqade.ir.routine.base import Routine
    from bloqade.ir.routine.params import Params
    from bloqade.ir.analog_circuit import AnalogCircuit

    atom_arrangement = start.add_position([(0, 0), (0, 6)])

    seq_seg_1 = start.rydberg.detuning.uniform.linear(0, 15, 0.1).parse_sequence()
    seq_seg_2 = start.rydberg.detuning.uniform.linear(15, 15, "dur").parse_sequence()
    seq_seg_3 = start.rydberg.detuning.uniform.linear(15, 0, 0.1).parse_sequence()

    sequence = seq_seg_1.append(seq_seg_2).append(seq_seg_3)
    circuit = AnalogCircuit(atom_arrangement=atom_arrangement, sequence=sequence)

    params = Params(2, {"dur": 0}, [], [])
    routine = Routine(source=None, circuit=circuit, params=params)
    routine.braket.local_emulator().run(shots=10)


"""
from bloqade.ir.location import Square
if __name__ == "__main__":
    simulator_job = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "run_time", 0.1], [0, 15, 15, 0]
        )
        .batch_assign(run_time=np.linspace(0.1, 3.8, 20))
        .braket_local_simulator(1000)
    )

    rydberg_densities = simulator_job.run_async().report().rydberg_densities()

    rydberg_densities = (
        simulator_job.run_async(multiprocessing=True).report().rydberg_densities()
    )

    # durations for rabi and detuning
    durations = [0.3, 1.6, 0.3]

    mis_udg_program = (
        Square(4, 5.5)
        .apply_defect_density(0.5)
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations, [0.0, 15.0, 15.0, 0.0]
        )
        .detuning.uniform.piecewise_linear(
            durations, [-30, -30, "final_detuning", "final_detuning"]
        )
    )

    mis_udg_job = mis_udg_program.batch_assign(final_detuning=np.linspace(0, 80, 81))

    hw_job = mis_udg_job.braket_local_simulator(100).run_async()
"""
