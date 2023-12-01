from collections import OrderedDict
from bloqade.ir import (
    rydberg,
    detuning,
    hyperfine,
    Sequence,
    Field,
    Pulse,
    Uniform,
    Linear,
    # ScaledLocations,
    LevelCoupling,
)
from bloqade.ir.control import sequence
from bloqade.ir.control.sequence import NamedSequence
from bloqade.ir import Interval
import pytest
from bloqade import cast
from io import StringIO
from IPython.lib.pretty import PrettyPrinter as PP
import bloqade.ir.tree_print as trp

trp.color_enabled = False


def test_lvlcouple_base():
    lc = LevelCoupling()
    assert lc.children() == []


def test_lvlcouple_hf():
    lc = hyperfine

    assert lc.print_node() == "HyperfineLevelCoupling"

    mystdout = StringIO()
    p = PP(mystdout)
    lc._repr_pretty_(p, 2)

    assert mystdout.getvalue() == "HyperfineLevelCoupling\n"


def test_lvlcouple_ryd():
    lc = rydberg

    assert lc.print_node() == "RydbergLevelCoupling"

    mystdout = StringIO()
    p = PP(mystdout)
    lc._repr_pretty_(p, 2)

    assert mystdout.getvalue() == "RydbergLevelCoupling\n"


def test_sequence():
    # seq empty
    seq = Sequence.create()
    assert seq.pulses == {}

    # seq non-lvlcoupling:
    with pytest.raises(TypeError):
        Sequence.create({"c": {}})

    # seq non-lvlcoupling:
    with pytest.raises(TypeError):
        Sequence.create({rydberg: 3.3})

    # seq full
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    assert seq_full.children() == {"RydbergLevelCoupling": ps}
    assert seq_full.print_node() == "Sequence"
    assert seq_full.duration == cast(3.0)
    assert hash(seq_full) == hash(Sequence) ^ hash(frozenset(seq_full.pulses.items()))

    mystdout = StringIO()
    p = PP(mystdout)
    seq_full._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue() == "Sequence\n"
        "└─ RydbergLevelCoupling\n"
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


def test_named_sequence():
    # seq full
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    # named seq:
    named = NamedSequence("qq", seq_full)

    assert named.children() == OrderedDict([("name", "qq"), ("sequence", seq_full)])
    assert named.print_node() == "NamedSequence"
    assert named.duration == cast(3.0)
    assert hash(named) == hash(NamedSequence) ^ hash(seq_full) ^ hash("qq")

    mystdout = StringIO()
    p = PP(mystdout)
    named._repr_pretty_(p, 10)
    print(repr(mystdout.getvalue()))
    assert (
        mystdout.getvalue() == "NamedSequence\n"
        "├─ name\n"
        "│  ⇒ qq\n"
        "└─ sequence\n"
        "   ⇒ Sequence\n"
        "     └─ RydbergLevelCoupling\n"
        "        ⇒ Pulse\n"
        "          └─ Detuning\n"
        "             ⇒ Field\n"
        "               └─ Drive\n"
        "                  ├─ modulation\n"
        "                  │  ⇒ UniformModulation\n"
        "                  └─ waveform\n"
        "                     ⇒ Linear\n"
        "                       ├─ start\n"
        "                       │  ⇒ Literal: 1.0\n"
        "                       ├─ stop\n"
        "                       │  ⇒ Variable: x\n"
        "                       └─ duration\n"
        "                          ⇒ Literal: 3.0"
    )


def test_slice_sequence():
    f = Field({Uniform: Linear(start=1.0, stop=2.0, duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})
    itvl = Interval(cast(0), cast(1.5))

    # slice:
    slc = seq_full[0:1.5]

    assert slc.children() == [itvl, seq_full]
    assert slc.print_node() == "Slice"
    assert slc.duration == cast(3.0)[itvl.start : itvl.stop]
    assert hash(slc) == hash(sequence.Slice) ^ hash(slc.sequence) ^ hash(itvl)

    mystdout = StringIO()
    p = PP(mystdout)
    slc._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue() == "Slice\n"
        "├─ Interval\n"
        "│  ├─ start\n"
        "│  │  ⇒ Literal: 0\n"
        "│  └─ stop\n"
        "│     ⇒ Literal: 1.5\n"
        "└─ Sequence\n"
        "   └─ RydbergLevelCoupling\n"
        "      ⇒ Pulse\n"
        "        └─ Detuning\n"
        "           ⇒ Field\n"
        "⋮\n"
    )


def test_append_sequence():
    f = Field({Uniform: Linear(start=1.0, stop=2.0, duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    app = seq_full.append(seq_full)

    assert app.children() == [seq_full, seq_full]
    assert app.print_node() == "Append"
    assert app.duration == cast(6.0)
    assert hash(app) == hash(sequence.Append) ^ hash(tuple([seq_full, seq_full]))

    mystdout = StringIO()
    p = PP(mystdout)
    app._repr_pretty_(p, 2)
    print(repr(mystdout.getvalue()))

    assert (
        mystdout.getvalue() == "Append\n"
        "├─ Sequence\n"
        "│  └─ RydbergLevelCoupling\n"
        "│     ⇒ Pulse\n"
        "│       └─ Detuning\n"
        "│          ⇒ Field\n"
        "⋮\n"
        "└─ Sequence\n"
        "   └─ RydbergLevelCoupling\n"
        "      ⇒ Pulse\n"
        "        └─ Detuning\n"
        "           ⇒ Field\n"
        "⋮\n"
    )
