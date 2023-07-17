from IPython.lib.pretty import PrettyPrinter as PP
from bloqade.ir import Linear
from io import StringIO


def test_printer():
    wf = Linear(start=0, stop=1, duration=1)

    mystdout = StringIO()
    p = PP(mystdout)

    wf._repr_pretty_(p, True)

    assert mystdout.getvalue() == "Linear\n⋮\n"
