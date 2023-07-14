from bloqade.ir import Field, Uniform, Linear, Pulse, detuning, rabi

from bloqade.ir.control.pulse import (
    FieldName,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
)


def test_fieldname_base():
    x = FieldName()

    assert x.children() == []


## from top to bottom test each hierarchy classes:
# rabi (RabiRouter) |- RabiAmplitude
#                   |- RabiPhase
def test_rabi_router():
    R = rabi

    assert R.print_node() == "RabiRouter"
    assert R.__repr__() == "rabi (amplitude, phase)"
    assert R.children() == {
        "Amplitude": RabiFrequencyAmplitude(),
        "Phase": RabiFrequencyPhase(),
    }


f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})

print(Pulse({detuning: f}))
print(Pulse({rabi.amplitude: f}))
print(Pulse({rabi.phase: f}))
print(Pulse({detuning: {Uniform: Linear(start=1.0, stop="x", duration=3.0)}}))
