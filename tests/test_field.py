from decimal import Decimal
from bloqade.ir import (
    Field,
    Uniform,
    Linear,
    ScaledLocations,
    Location,
    SpatialModulation,
    RunTimeVector,
    AssignedRunTimeVector,
)
from bloqade.ir.control.field import Drive
import pytest
from bloqade import cast
from io import StringIO
from IPython.lib.pretty import PrettyPrinter as PP

import bloqade.ir.tree_print as trp
from bloqade import tree_depth

trp.color_enabled = False

tree_depth(10)


def test_location():
    loc = Location(3)

    assert str(loc) == "Location(3)"
    assert loc.print_node() == "Location(3)"
    assert loc.children() == []


def test_spacmod_base():
    x = SpatialModulation()

    with pytest.raises(NotImplementedError):
        x.figure()

    assert x._get_data() == {}


def test_uniform():
    x = Uniform

    assert str(x) == "UniformModulation\n"
    assert x.print_node() == "UniformModulation"
    assert x.children() == []
    assert x._get_data() == (["uni"], ["all"])

    mystdout = StringIO()
    p = PP(mystdout)

    x._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "UniformModulation\n"


def test_runtime_vec():
    x = RunTimeVector("sss")

    assert str(x) == "RunTimeVector: sss\n"
    assert x.print_node() == "RunTimeVector: sss"
    assert x.children() == []
    assert x._get_data() == (["sss"], ["vec"])

    mystdout = StringIO()
    p = PP(mystdout)

    x._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "RunTimeVector: sss\n"


def test_assigned_runtime_vec():
    x = AssignedRunTimeVector("sss", [Decimal("1.0"), Decimal("2.0")])

    x_str = str(x)

    assert x_str == (
        "AssignedRunTimeVector: sss\n" "├─ Literal: 1.0\n" "└─ Literal: 2.0"
    )
    assert x.print_node() == "AssignedRunTimeVector: sss"
    assert x.children() == cast([Decimal("1.0"), Decimal("2.0")])
    assert x._get_data() == (["sss"], ["vec"])

    mystdout = StringIO()
    p = PP(mystdout)

    x._repr_pretty_(p, 0)

    assert mystdout.getvalue() == (
        "AssignedRunTimeVector: sss\n" "├─ Literal: 1.0\n" "⋮\n" "└─ Literal: 2.0⋮\n"
    )


def test_scal_loc():
    x = ScaledLocations.create({1: 1.0, 2: 2.0})

    with pytest.raises(ValueError):
        ScaledLocations.create({(2, 3): 2})

    assert x.print_node() == "ScaledLocations"
    assert x.children() == {"Location(1)": cast(1.0), "Location(2)": cast(2.0)}
    assert x._get_data() == (["loc[1]", "loc[2]"], ["1.0", "2.0"])

    x[Location(0)] = 1.0

    assert x[Location(0)] == cast(1.0)
    assert x

    mystdout = StringIO()
    p = PP(mystdout)

    x._repr_pretty_(p, 0)

    assert mystdout.getvalue() == (
        "ScaledLocations\n"
        "├─ Location(1)\n"
        "│  ⇒ Literal: 1.0\n"
        "⋮\n"
        "├─ Location(2)\n"
        "│  ⇒ Literal: 2.0\n"
        "⋮\n"
        "└─ Location(0)\n"
        "   ⇒ Literal: 1.0⋮\n"
    )


def test_field_scaled_locations():
    Loc = ScaledLocations.create({1: 1.0, 2: 2.0})
    Loc2 = ScaledLocations.create({3: 1.0, 4: 2.0})
    Loc3 = ScaledLocations.create({1: 1.0, 2: 2.0, 3: 1.0, 4: 2.0})
    f1 = Field({Loc: Linear(start=1.0, stop="x", duration=3.0)})
    f2 = Field({Loc: Linear(start=1.0, stop="x", duration=3.0)})
    f3 = Field({Loc2: Linear(start=1.0, stop="x", duration=3.0)})
    f4 = Field({Loc3: Linear(start="y", stop="x", duration=4.0)})
    f5 = Field({})

    # add with non field
    with pytest.raises(ValueError):
        f1.add(Loc)

    assert f5.duration == cast(0)
    assert f1.duration == cast(3.0)

    mystdout = StringIO()
    p = PP(mystdout)

    f1._repr_pretty_(p, 10)

    assert mystdout.getvalue() == (
        "Field\n"
        "└─ Drive\n"
        "   ├─ modulation\n"
        "   │  ⇒ ScaledLocations\n"
        "   │    ├─ Location(1)\n"
        "   │    │  ⇒ Literal: 1.0\n"
        "   │    └─ Location(2)\n"
        "   │       ⇒ Literal: 2.0\n"
        "   └─ waveform\n"
        "      ⇒ Linear\n"
        "        ├─ start\n"
        "        │  ⇒ Literal: 1.0\n"
        "        ├─ stop\n"
        "        │  ⇒ Variable: x\n"
        "        └─ duration\n"
        "           ⇒ Literal: 3.0"
    )

    # add with field same spat-mod
    o1 = f1.add(f2)
    assert len(o1.drives.keys()) == 1

    # add with field diff spat-mod
    o2 = f1.add(f3)
    assert o2 == Field({Loc3: Linear(start=1.0, stop="x", duration=3.0)})
    # assert len(o2.drives.keys()) == 1

    assert f2.print_node() == "Field"
    # assert type(hash(f1)) == int
    assert f1.children() == [Drive(k, v) for k, v in f1.drives.items()]

    assert hash(f1)

    o3 = f1.add(f4)
    assert o3 == Field(
        {
            Loc3: Linear(start="y", stop="x", duration=4.0),
            Loc: Linear(start=1.0, stop="x", duration=3.0),
        }
    )

    assert o3.duration == cast(3.0).max(4.0)
