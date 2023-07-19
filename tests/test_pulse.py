from bloqade.ir import Field, Uniform, Linear, Pulse, NamedPulse, detuning, rabi
from bloqade.ir import Interval
from bloqade import cast
import pytest
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


def test_rabi_amp_phase():
    rf = RabiFrequencyAmplitude()
    rp = RabiFrequencyPhase()
    assert rf.print_node() == "RabiFrequencyAmplitude"
    assert rp.print_node() == "RabiFrequencyPhase"


def test_detune():
    D = detuning

    assert D.print_node() == "Detuning"


def test_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})

    ## make pulse, invalid field:
    with pytest.raises(TypeError):
        Pulse({Uniform: 1.0})

    ## make pulse:
    ps1 = Pulse({detuning: f})

    assert ps1.print_node() == "Pulse"
    assert ps1.children() == {"Detuning": f}


def test_named_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps1 = Pulse({detuning: f})
    ps = NamedPulse("qq", ps1)

    assert ps.__repr__() == "NamedPulse(name='qq', pulse=%s)" % (ps1.__repr__())

    assert ps.children() == {"Name": "qq", "Pulse": ps1}


def test_slice_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps1 = Pulse({detuning: f})
    itvl = Interval(cast(0), cast(1.5))

    ## invoke slice
    ps = ps1.slice(itvl)

    assert ps.__repr__() == "%s[%s]" % (ps1.__repr__(), itvl.__repr__())
    assert ps.print_node() == "Slice"
    assert ps.children() == {"Pulse": ps1, "Interval": itvl}


def test_append_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps1 = Pulse({detuning: f})

    # invoke append:
    ps = ps1.append(ps1)

    assert ps.__repr__() == "pulse.Append(value=[%s, %s])" % (
        ps1.__repr__(),
        ps1.__repr__(),
    )
    assert ps.children() == [ps1, ps1]


# print(Pulse({detuning: f}))
# print(Pulse({rabi.amplitude: f}))
# print(Pulse({rabi.phase: f}))
# print(Pulse({detuning: {Uniform: Linear(start=1.0, stop="x", duration=3.0)}}))
