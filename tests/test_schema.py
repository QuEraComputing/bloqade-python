from bloqade.codegen.hardware.waveform import WaveformCodeGen
from bloqade.codegen.hardware.field import FieldCodeGen
from bloqade.codegen.hardware.pulse import PulseCodeGen

from bloqade.ir.pulse import RabiFrequencyAmplitude, RabiFrequencyPhase
from bloqade.ir.scalar import cast
from bloqade.ir.waveform import Constant, Linear, Append
from bloqade.ir.field import Field, Global
from bloqade.ir.sequence import Pulse, RydbergLevelCoupling


initial_detuning =  cast("initial_detuning")
final_detuning = cast("final_detuning")
up_time = cast("up_time")
anneal_time = cast("anneal_time")

detuning_wf = Append(
        [
            Constant(initial_detuning, up_time),
            Linear(initial_detuning, final_detuning, anneal_time),  
            Constant(final_detuning, up_time)
        ]
    )

variable_reference = dict(
    initial_detuning = -15,
    final_detuning = 10,
    up_time = 0.1,
    anneal_time = 4.0
)

wf_codegen = WaveformCodeGen(10, variable_reference, field_name = RabiFrequencyAmplitude())

times, values = wf_codegen.emit(detuning_wf[0.05:4.15])

print(times)
print(values)

field = Field({Global: detuning_wf})

field_codegen = FieldCodeGen(
    10, variable_reference, field_name=RabiFrequencyAmplitude(),
)
quera_field = field_codegen.emit(field)

print(quera_field)


field = Field({Global: detuning_wf})
field_codegen = FieldCodeGen(
    10, variable_reference, field_name=RabiFrequencyPhase(),
)
try:
    quera_field = field_codegen.emit(field)
except NotImplementedError:
    pass

pulse = Pulse({RabiFrequencyAmplitude():field})


pulse_codegen = PulseCodeGen(10, variable_reference, level_coupling=RydbergLevelCoupling())
rydberg_hamiltonian = pulse_codegen.emit(pulse)
print(rydberg_hamiltonian)