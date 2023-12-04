from bloqade.ir import Field, Uniform, Linear, Pulse, NamedPulse, detuning, rabi
from bloqade.ir import Interval
from bloqade import cast
import pytest
from io import StringIO
from IPython.lib.pretty import PrettyPrinter as PP
from bloqade.ir.control import pulse
from bloqade.ir.control.pulse import (
    FieldName,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
)
import bloqade.ir.tree_print as trp

trp.color_enabled = False


def test_fieldname_base():
    x = FieldName()

    assert x.children() == []


## from top to bottom test each hierarchy classes:
# rabi (RabiRouter) |- RabiAmplitude
#                   |- RabiPhase
def test_rabi_router():
    R = rabi

    assert R.print_node() == "RabiRouter"
    assert R.children() == {
        "Amplitude": RabiFrequencyAmplitude(),
        "Phase": RabiFrequencyPhase(),
    }

    mystdout = StringIO()
    p = PP(mystdout)

    R._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue()
        == "RabiRouter\n"
        + "├─ Amplitude\n"
        + "│  ⇒ RabiFrequencyAmplitude\n"
        + "└─ Phase\n"
        + "   ⇒ RabiFrequencyPhase"
    )


def test_rabi_amp_phase():
    rf = RabiFrequencyAmplitude()

    assert rf.print_node() == "RabiFrequencyAmplitude"

    mystdout = StringIO()
    p = PP(mystdout)

    rf._repr_pretty_(p, 10)

    assert mystdout.getvalue() == "RabiFrequencyAmplitude\n"

    rp = RabiFrequencyPhase()
    assert rp.print_node() == "RabiFrequencyPhase"

    mystdout = StringIO()
    p = PP(mystdout)

    rp._repr_pretty_(p, 10)

    assert mystdout.getvalue() == "RabiFrequencyPhase\n"


def test_detune():
    D = detuning

    assert D.print_node() == "Detuning"

    mystdout = StringIO()
    p = PP(mystdout)

    D._repr_pretty_(p, 10)

    assert mystdout.getvalue() == "Detuning\n"


def test_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})

    ## make pulse, invalid field:
    with pytest.raises(TypeError):
        Pulse.create({Uniform: 1.0})

    ## make pulse:
    ps1 = Pulse({detuning: f})

    assert ps1.print_node() == "Pulse"
    assert ps1.children() == {"Detuning": f}
    assert ps1.duration == cast(3.0).max(cast(0))

    assert hash(ps1) == hash(Pulse) ^ hash(frozenset([(detuning, f)]))

    mystdout = StringIO()
    p = PP(mystdout)

    ps1._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue() == "Pulse\n"
        "└─ Detuning\n"
        "   ⇒ Field\n"
        "     └─ Drive\n"
        "        ├─ modulation\n"
        "        │  ⇒ UniformModulation\n"
        "        └─ waveform\n"
        "           ⇒ Linear\n"
        "             ├─ start\n"
        "             │  ⇒ Literal: 1.0\n"
        "             ├─ stop\n"
        "             │  ⇒ Variable: x\n"
        "             └─ duration\n"
        "                ⇒ Literal: 3.0"
    )


def test_named_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps1 = Pulse({detuning: f})
    ps = NamedPulse("qq", ps1)

    assert ps.children() == {"Name": "qq", "Pulse": ps1}
    assert ps.print_node() == "NamedPulse"
    assert ps.duration == cast(0.0).max(cast(3.0))

    assert hash(ps) == hash(NamedPulse) ^ hash(ps.name) ^ hash(ps.pulse)

    mystdout = StringIO()
    p = PP(mystdout)

    ps._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue() == "NamedPulse\n"
        "├─ Name\n"
        "│  ⇒ qq\n"
        "└─ Pulse\n"
        "   ⇒ Pulse\n"
        "     └─ Detuning\n"
        "        ⇒ Field\n"
        "          └─ Drive\n"
        "             ├─ modulation\n"
        "             │  ⇒ UniformModulation\n"
        "             └─ waveform\n"
        "                ⇒ Linear\n"
        "                  ├─ start\n"
        "                  │  ⇒ Literal: 1.0\n"
        "                  ├─ stop\n"
        "                  │  ⇒ Variable: x\n"
        "                  └─ duration\n"
        "                     ⇒ Literal: 3.0"
    )


def test_slice_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps1 = Pulse({detuning: f})
    itvl = Interval(cast(0), cast(1.5))

    ## invoke slice
    ps = ps1.slice(itvl)

    assert ps.print_node() == "Slice"
    assert ps.children() == {"Pulse": ps1, "Interval": itvl}
    assert ps.duration == cast(0).max(cast(3.0))[itvl.start : itvl.stop]
    assert hash(ps) == hash(pulse.Slice) ^ hash(ps.pulse) ^ hash(ps.interval)

    mystdout = StringIO()
    p = PP(mystdout)

    ps._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue() == "Slice\n"
        "├─ Pulse\n"
        "│  ⇒ Pulse\n"
        "│    └─ Detuning\n"
        "│       ⇒ Field\n"
        "│         └─ Drive\n"
        "│            ├─ modulation\n"
        "│            │  ⇒ UniformModulation\n"
        "│            └─ waveform\n"
        "│               ⇒ Linear\n"
        "│                 ├─ start\n"
        "│                 │  ⇒ Literal: 1.0\n"
        "│                 ├─ stop\n"
        "│                 │  ⇒ Variable: x\n"
        "│                 └─ duration\n"
        "│                    ⇒ Literal: 3.0\n"
        "└─ Interval\n"
        "   ⇒ Interval\n"
        "     ├─ start\n"
        "     │  ⇒ Literal: 0\n"
        "     └─ stop\n"
        "        ⇒ Literal: 1.5"
    )


def test_append_pulse():
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps1 = Pulse({detuning: f})

    # invoke append:
    ps = ps1.append(ps1)

    assert ps.children() == [ps1, ps1]
    assert ps.print_node() == "Append"
    assert ps.duration == cast(0).max(cast(3.0)) + cast(0).max(cast(3.0))
    assert hash(ps) == hash(pulse.Append) ^ hash(tuple(ps.pulses))

    mystdout = StringIO()
    p = PP(mystdout)

    ps._repr_pretty_(p, 10)
    print(repr(mystdout.getvalue()))
    assert (
        mystdout.getvalue() == "Append\n"
        "├─ Pulse\n"
        "│  └─ Detuning\n"
        "│     ⇒ Field\n"
        "│       └─ Drive\n"
        "│          ├─ modulation\n"
        "│          │  ⇒ UniformModulation\n"
        "│          └─ waveform\n"
        "│             ⇒ Linear\n"
        "│               ├─ start\n"
        "│               │  ⇒ Literal: 1.0\n"
        "│               ├─ stop\n"
        "│               │  ⇒ Variable: x\n"
        "│               └─ duration\n"
        "│                  ⇒ Literal: 3.0\n"
        "└─ Pulse\n"
        "   └─ Detuning\n"
        "      ⇒ Field\n"
        "        └─ Drive\n"
        "           ├─ modulation\n"
        "           │  ⇒ UniformModulation\n"
        "           └─ waveform\n"
        "              ⇒ Linear\n"
        "                ├─ start\n"
        "                │  ⇒ Literal: 1.0\n"
        "                ├─ stop\n"
        "                │  ⇒ Variable: x\n"
        "                └─ duration\n"
        "                   ⇒ Literal: 3.0"
    )


# print(Pulse({detuning: f}))
# print(Pulse({rabi.amplitude: f}))
# print(Pulse({rabi.phase: f}))
# print(Pulse({detuning: {Uniform: Linear(start=1.0, stop="x", duration=3.0)}}))
