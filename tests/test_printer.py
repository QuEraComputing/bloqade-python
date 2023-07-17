from IPython.lib.pretty import PrettyPrinter as PP
from bloqade.ir import Linear
from io import StringIO
from bloqade.ir.tree_print import Printer


def test_printer():
    wf = Linear(start=0, stop=1, duration=1)

    mystdout = StringIO()
    p = PP(mystdout)

    wf._repr_pretty_(p, True)

    assert mystdout.getvalue() == "Linear\n⋮\n"


def test_printer_nodes():
    wf = Linear(start=0, stop=1, duration=1)
    wf2 = wf + (wf + wf)

    mystdout = StringIO()
    p = PP(mystdout)

    pr = Printer(p)
    children = wf2.children().copy()  # children is list so no print children
    assert pr.should_print_annotation(children) is False
