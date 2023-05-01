from bloqade.codegen.hardware.waveform import WaveformCodeGen
from bloqade.ir.pulse import FieldName
from bloqade.ir.scalar import cast
from bloqade.ir.waveform import Constant, Linear, Append


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

wf_codegen = WaveformCodeGen(10, variable_reference, field_name = FieldName.RabiFrequencyAmplitude)

times, values = wf_codegen.emit(detuning_wf)

print(times)
print(values)