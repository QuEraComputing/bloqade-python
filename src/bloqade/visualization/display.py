from bokeh.models import Div
from bokeh.layouts import row, column
from bokeh.io import show
from bloqade.visualization import report_visualize


def liner(txt):
    return f"<p>{txt}</p>"


def display_builder(analog_circ, metas, batch_id: int):
    kwargs = metas.static_params
    kwargs.update(metas.batch_params[batch_id])

    out = "<p>Assignments: </p>"
    for key, val in kwargs.items():
        out += liner(f" :: {key} = {val}")

    rowobj = analog_circ.figure(**kwargs)

    field = rowobj.children[0]
    reg = rowobj.children[1]
    div = Div(text=out, width=200, height=200)

    show(row(field, column(reg, div)))


def display_analog_circuit(analog_circuit, assignments):
    show(row(*analog_circuit.figure(**assignments)))


def display_pulse(pulse, assignments):
    show(pulse.figure(**assignments))


def display_sequence(sequence, assignments):
    show(sequence.figure(**assignments))


def display_field(field, assignments):
    show(field.figure(**assignments))


def display_report(report):
    dat = report_visualize.format_report_data(report)
    p = report_visualize.report_visual(*dat)
    show(p)
