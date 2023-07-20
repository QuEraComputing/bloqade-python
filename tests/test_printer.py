from IPython.lib.pretty import PrettyPrinter as PP
from bloqade.ir import Linear, Poly
from io import StringIO
from bloqade.ir.tree_print import Printer
from bloqade import xprint


def test_xprint():
    wf = Linear(start=0, stop=1, duration=1)

    mystdout = StringIO()
    xprint(wf, iostream=mystdout)

    assert (
        mystdout.getvalue()
        == "Linear\n├─ start ⇒ Literal: 0\n├─ stop ⇒ Literal: 1\n"
        + "└─ duration ⇒ Literal: 1\n"
    )

    s = [1, 2, 3]
    mystdout = StringIO()
    xprint(s, iostream=mystdout)


def test_printer():
    wf = Linear(start=0, stop=1, duration=1)

    mystdout = StringIO()
    p = PP(mystdout)

    wf._repr_pretty_(p, 1)

    assert (
        mystdout.getvalue()
        == "Linear\n├─ start ⇒ Literal: 0\n├─ stop ⇒ Literal: 1\n"
        + "└─ duration ⇒ Literal: 1"
    )


def test_printer_nodes_list():
    wf = Linear(start=0, stop=1, duration=1)
    wf2 = wf + (wf + wf)

    mystdout = StringIO()
    p = PP(mystdout)

    pr = Printer(p)
    children = wf2.children().copy()  # children is list so no print children
    assert pr.should_print_annotation(children) is False


def test_printer_nodes_dict():
    wf = Poly([1, 2, 3], duration=1)

    mystdout = StringIO()
    p = PP(mystdout)

    pr = Printer(p)
    children = wf.children().copy()  # children is list so no print children

    assert pr.should_print_annotation(children) is True
    wf._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue()
        == "Poly\n├─ b ⇒ Literal: 1\n├─ t ⇒ Literal: 2\n"
        + "├─ t^2 ⇒ Literal: 3\n└─ duration ⇒ Literal: 1"
    )


def test_printer_nodes_compose_turncate():
    wf = Poly([1, 2, 3], duration=1)
    wf1 = Linear(start=0, stop=1, duration=1)
    wf2 = wf + (wf[:0.5] + wf1)

    mystdout = StringIO()
    p = PP(mystdout)

    wf2._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "+\n├─ Poly\n⋮\n└─ +\n⋮\n"


def test_printer_nodes_compose_all():
    wf = Poly([1, 2, 3], duration=1)
    wf1 = Linear(start=0, stop=1, duration=1)
    wf2 = wf + (wf[:0.5] + wf1)

    mystdout = StringIO()
    p = PP(mystdout)

    wf2._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue()
        == "+\n├─ Poly\n│  ├─ b ⇒ Literal: 1\n│  ├─ t ⇒ Literal: 2\n"
        + "│  ├─ t^2 ⇒ Literal: 3\n│  └─ duration ⇒ Literal: 1\n"
        + "└─ +\n   ├─ Slice\n   │  ├─ Poly\n   │  │  ├─ b ⇒ Literal: 1\n"
        + "   │  │  ├─ t ⇒ Literal: 2\n   │  │  ├─ t^2 ⇒ Literal: 3\n"
        + "   │  │  └─ duration ⇒ Literal: 1\n   │  └─ Interval\n"
        + "   │     └─ stop ⇒ Literal: 0.5\n   └─ Linear\n      ├─ start ⇒ Literal: 0\n"
        + "      ├─ stop ⇒ Literal: 1\n      └─ duration ⇒ Literal: 1"
    )
