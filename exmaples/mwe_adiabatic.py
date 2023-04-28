from bloqade.ir.scalar import cast
import bloqade.ir.waveform as wf
import bloqade.ir.pulse as pulse
import bloqade.ir.sequence as sequence 

from bloqade.ir.shape import Constant, Linear
from bloqade.ir.field import Global, Field
from bloqade.ir.field import RabiFrequencyAmplitude, Detuning
from bloqade.ir.sequence import Rydberg
from bloqade.lattice import square_lattice

rabi_amplitude_max = cast("rabi_amplitude_max")
initial_detuning =  cast("initial_detuning")
final_detuning = cast("final_detuning")
up_time = cast("up_time")
anneal_time = cast("anneal_time")
zero = cast(0.0)

# syntax options
detuning_wf = wf.Sequence(Constant(initial_detuning), up_time)\
    .append(
        wf.Sequence(Linear(initial_detuning, final_detuning), anneal_time)
    )\
    .append(
        wf.Sequence(Constant(final_detuning), up_time)
    )

wf.concatenate(
    [
        wf.Sequence(Constant(initial_detuning), up_time),
        wf.Sequence(Linear(initial_detuning, final_detuning), anneal_time),
        wf.Sequence(Constant(final_detuning), up_time)
    ]
)

detuning_wf = wf.Sequence(Constant(initial_detuning), up_time)\
    .extend([
        wf.Sequence(Linear(initial_detuning, final_detuning), anneal_time),
        wf.Sequence(Constant(final_detuning), up_time)
    ])

rabi_wf = wf.concatenate(
    [
        wf.Sequence(Linear(zero, rabi_amplitude_max), up_time),
        wf.Sequence(Constant(rabi_amplitude_max, rabi_amplitude_max), anneal_time),
         wf.Sequence(Linear(rabi_amplitude_max, zero), up_time)
    ]
)
    

detuning_field = Field({Global: detuning_wf})
rabi_field = Field({Global: rabi_wf})

adiabatic_pulse = pulse.Instruction(
        {
            RabiFrequencyAmplitude:rabi_field,
            Detuning: detuning_field  
        }
    )

adiabatic_sequence = sequence.Sequence(
    Rydberg: adiabatic_pulse
)

lattice = square_lattice(6,6,lattice_spacing = cast("lattice_spacing"))

# expose this with a config file. 
params = dict(
    shots=1000,
    initial_detuning = -15,
    final_detuning = 15,
    rabi_amplitude_max = 15,
    up_time = 0.1,
    anneal_time = 3.8,
    lattice_spacing = 6.1
)

rydberg_occ = lattice\
    .add_sequence(adiabatic_sequence)\
    .task(**params)\
    .submit()\
    .result()\
    .post_process()\
    .local_rydberg_density()


# with config file


rydberg_occ = lattice\
    .add_sequence(adiabatic_sequence)\
    .batch_task(config_file = "...")\
    .submit()\
    .result()\
    .post_process()\
    .local_rydberg_density()




