from IPython.lib.pretty import PrettyPrinter as PP
from bloqade.ir import Linear, Poly
from io import StringIO
from bloqade.ir.tree_print import Printer


def test_printer():
    wf = Linear(start=0, stop=1, duration=1)

    mystdout = StringIO()
    p = PP(mystdout)

    wf._repr_pretty_(p, 1)

    assert (
        mystdout.getvalue()
        == "Linear\n"
        + "├─ start\n"
        + "│  ⇒ Literal: 0\n"
        + "├─ stop\n"
        + "│  ⇒ Literal: 1\n"
        + "└─ duration\n"
        + "   ⇒ Literal: 1"
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
        == "Poly\n"
        + "├─ b\n"
        + "│  ⇒ Literal: 1\n"
        + "├─ t\n"
        + "│  ⇒ Literal: 2\n"
        + "├─ t^2\n"
        + "│  ⇒ Literal: 3\n"
        + "└─ duration\n"
        + "   ⇒ Literal: 1"
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
        == "+\n"
        + "├─ Poly\n"
        + "│  ├─ b\n"
        + "│  │  ⇒ Literal: 1\n"
        + "│  ├─ t\n"
        + "│  │  ⇒ Literal: 2\n"
        + "│  ├─ t^2\n"
        + "│  │  ⇒ Literal: 3\n"
        + "│  └─ duration\n"
        + "│     ⇒ Literal: 1\n"
        + "└─ +\n"
        + "   ├─ Slice\n"
        + "   │  ├─ Poly\n"
        + "   │  │  ├─ b\n"
        + "   │  │  │  ⇒ Literal: 1\n"
        + "   │  │  ├─ t\n"
        + "   │  │  │  ⇒ Literal: 2\n"
        + "   │  │  ├─ t^2\n"
        + "   │  │  │  ⇒ Literal: 3\n"
        + "   │  │  └─ duration\n"
        + "   │  │     ⇒ Literal: 1\n"
        + "   │  └─ Interval\n"
        + "   │     └─ stop\n"
        + "   │        ⇒ Literal: 0.5\n"
        + "   └─ Linear\n"
        + "      ├─ start\n"
        + "      │  ⇒ Literal: 0\n"
        + "      ├─ stop\n"
        + "      │  ⇒ Literal: 1\n"
        + "      └─ duration\n"
        + "         ⇒ Literal: 1"
    )
