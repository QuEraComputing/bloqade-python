from bokeh.models import Div
from bokeh.layouts import row, column
from bokeh.io import show
from bloqade.visualization import report_visualize
from bokeh.models import (
    NumericInput,
    Button,
    CustomJS,
)


## unify the entry point:
def display_ir(obj, assignments):
    from bloqade.ir.analog_circuit import AnalogCircuit
    from bloqade.ir.control.pulse import PulseExpr
    from bloqade.ir.control.sequence import SequenceExpr
    from bloqade.ir.control.field import Field, SpatialModulation
    from bloqade.ir.control.waveform import Waveform
    from bloqade.ir.location import AtomArrangement

    if isinstance(obj, AnalogCircuit):
        display_analog_circuit(obj, assignments)
    elif isinstance(obj, PulseExpr):
        display_pulse(obj, assignments)
    elif isinstance(obj, SequenceExpr):
        display_sequence(obj, assignments)
    elif isinstance(obj, Field):
        display_field(obj, assignments)
    elif isinstance(obj, SpatialModulation):
        display_spatialmod(obj, assignments)
    elif isinstance(obj, Waveform):
        display_waveform(obj, assignments)
    elif isinstance(obj, AtomArrangement):
        display_atom_arrangement(obj, assignments)
    else:
        raise NotImplementedError(f"not supported IR for display, got {type(obj)}")


def figure_ir(obj, assignments):
    from bloqade.ir.analog_circuit import AnalogCircuit
    from bloqade.ir.control.pulse import PulseExpr
    from bloqade.ir.control.sequence import SequenceExpr
    from bloqade.ir.control.field import Field, SpatialModulation
    from bloqade.ir.control.waveform import Waveform
    from bloqade.ir.location import AtomArrangement

    if isinstance(obj, AnalogCircuit):
        return analog_circuit_figure(obj, assignments)
    elif isinstance(obj, PulseExpr):
        return obj.figure(**assignments)
    elif isinstance(obj, SequenceExpr):
        return obj.figure(**assignments)
    elif isinstance(obj, Field):
        return obj.figure(**assignments)
    elif isinstance(obj, SpatialModulation):
        return obj.figure(**assignments)
    elif isinstance(obj, Waveform):
        return obj.figure(**assignments)
    elif isinstance(obj, AtomArrangement):
        return atom_arrangement_figure(obj, assignments)
    else:
        raise NotImplementedError(f"not supported IR for display, got {type(obj)}")


def liner(txt):
    return f"<p>{txt}</p>"


def builder_figure(builder, batch_id):
    from bloqade.builder.parse.builder import Parser

    routine = Parser().parse(builder)

    analog_circ = routine.circuit
    metas = routine.params

    kwargs = metas.static_params
    kwargs.update(metas.batch_params[batch_id])

    out = "<p>Assignments: </p>"
    for key, val in kwargs.items():
        out += liner(f" :: {key} = {val}")

    field, reg = analog_circ.figure(**kwargs)

    div = Div(text=out, width=200, height=200)
    return row(field, column(reg, div))


def display_builder(builder, batch_id):
    fig = builder_figure(builder, batch_id)
    show(fig)


## ir
def analog_circuit_figure(analog_circuit, assignments):
    return row(*analog_circuit.figure(**assignments))


def display_analog_circuit(analog_circuit, assignments):
    fig = analog_circuit_figure(analog_circuit, assignments)
    show(fig)


def display_pulse(pulse, assignments):
    show(pulse.figure(**assignments))


def display_sequence(sequence, assignments):
    show(sequence.figure(**assignments))


def display_field(field, assignments):
    show(field.figure(**assignments))


def display_spatialmod(spmod, assignments):
    show(spmod.figure(**assignments))


def display_waveform(wvfm_ir, assignments):
    show(wvfm_ir.figure(**assignments))


def atom_arrangement_figure(atom_arrangement, assignments):
    """show the register."""
    p = atom_arrangement.figure(None, **assignments)

    # get the Blocade rad object
    cr = None
    for rd in p.renderers:
        if rd.name == "Brad":
            cr = rd

    # adding rydberg radis input
    Brad_input = NumericInput(
        value=0, low=0, title="Blockade radius (um):", mode="float"
    )

    # js link toggle btn
    toggle_button = Button(label="Toggle")
    toggle_button.js_on_event(
        "button_click",
        CustomJS(args=dict(cr=cr), code="""cr.visible = !cr.visible;"""),
    )

    # js link radius
    Brad_input.js_link("value", cr.glyph, "radius")

    full = column(p, row(Brad_input, toggle_button))
    # full.sizing_mode="scale_both"
    return full


def display_atom_arrangement(atom_arrangement, assignments):
    fig = atom_arrangement_figure(atom_arrangement, assignments)
    show(fig)


## report


def report_figure(report):
    dat = report_visualize.format_report_data(report)
    p = report_visualize.report_visual(*dat)
    return p


def display_report(report):
    fig = report_figure(report)
    show(fig)


## task_ir
def display_task_ir(task_ir):
    show(task_ir.figure())
