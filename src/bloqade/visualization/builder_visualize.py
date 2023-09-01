from bokeh.models import Div
from bokeh.layouts import row, column
from bokeh.io import show


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
