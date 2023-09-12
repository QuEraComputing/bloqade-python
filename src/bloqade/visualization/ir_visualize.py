from bokeh.plotting import figure
from bokeh.layouts import row, column
from bokeh.models import CustomJS, MultiChoice
from bokeh.models import (
    ColumnDataSource,
    DataCube,
    GroupingInfo,
    StringFormatter,
    TableColumn,
)
from bokeh.models import Tabs, TabPanel, HoverTool, Div, CrosshairTool, Span
from bokeh.palettes import Dark2_5
import itertools
import numpy as np
from typing import List


def mock_data(Ndata):
    out = []
    ch_names = []

    d0 = []
    d1 = []
    scl = []
    unicnt = 0
    for i in range(Ndata):
        x = np.linspace(0, 10, 200)
        y = np.random.normal(size=len(x))
        name = None

        locs = []  # str
        scales = []  # float
        Nloc = np.random.randint(5)
        if Nloc == 0:
            # unifom
            name = "uni[%d]" % (unicnt)
            unicnt += 1
            locs = ["all"]
            scales = [1.0]
        else:
            locs_idx = np.unique(np.random.randint(10, size=Nloc)).flatten()
            locs = ["loc[%d]" % (n) for n in locs_idx]
            scales = np.random.rand(len(locs)).flatten()
            name = "ch[%d]" % (i)

        d0 += [name] * len(locs)
        d1 += list(locs)
        scl += list(scales)

        ch_names.append(name)
        lbl = [name] * len(x)
        out.append(ColumnDataSource(data=dict(wvfm_x=x, wvfm_y=y, lbl=lbl)))

    spmod_source = ColumnDataSource(
        data=dict(
            d0=d0,
            d1=d1,
            px=scl,
        )
    )

    return out, ch_names, spmod_source


def mock_register():
    p = figure(width=300, height=300, toolbar_location="above")
    p.circle(x=np.random.rand(10), y=np.random.rand(10))

    return p


def Field_wvfm(colors, data_sources, ch_names, crx_hair_overlay: List = None):
    p = figure(width=800, height=170)

    # add plots of data:
    glyph_obj = []
    Ndata = len(data_sources)
    for i, color in zip(range(Ndata), colors):
        obj = p.line(
            x="wvfm_x",
            y="wvfm_y",
            source=data_sources[i],
            name="data%d" % (i),
            color=color,
            visible=False,
        )
        glyph_obj.append(obj)

    p.xaxis.axis_label = "Time (us)"

    # add tools:
    # hover:
    hov_tool = HoverTool(mode="vline")
    hov_tool.tooltips = [("(x,y)", "(@wvfm_x, @wvfm_y)"), ("channel", "@lbl")]
    p.add_tools(hov_tool)

    # crosshair:
    if crx_hair_overlay is None:
        crx_hair = CrosshairTool(dimensions="height")
    else:
        crx_hair = CrosshairTool(overlay=crx_hair_overlay)

    p.add_tools(crx_hair)

    # add multi choice for select channel:
    glyph_obj[0].visible = True
    multi_choice = MultiChoice(value=[ch_names[0]], options=ch_names)
    multi_choice.js_on_change(
        "value",
        CustomJS(
            args=dict(glyphobj=glyph_obj, ch_names=ch_names, nelem=len(ch_names)),
            code="""
                                const vals = this.value
                                for(let i=0;i<nelem;i++){
                                    glyphobj[i].visible=false;
                                    for(let j=0;j<vals.length;j++){
                                        if(vals[j]==ch_names[i]){
                                            glyphobj[i].visible=true;
                                            break;
                                        }
                                    }
                                }
                              """,
        ),
    )

    # compose layout:
    return column(multi_choice, p)


def SpacialMod(spmod_data):
    # setting:
    formatter = StringFormatter(font_style="bold")
    target = ColumnDataSource(data=dict(row_indices=[], labels=[]))  # this is needed
    columns = [
        TableColumn(
            field="d1", title="Channel", width=20, sortable=False, formatter=formatter
        ),
        TableColumn(field="px", title="Scale", width=20, sortable=False),
    ]
    grouping = [GroupingInfo(getter="d0")]

    # generate table:
    cube = DataCube(
        source=spmod_data,
        columns=columns,
        grouping=grouping,
        target=target,
        width=200,
        height=170,
    )

    return cube


def assemble_field(left_spmod, right_waveform, title):
    # add div:
    frame = row(left_spmod, right_waveform)
    div = Div(text=title, width=frame.width, height=10)
    return column(div, frame)


def assemble_pulse_panel(field_plots: List, title: str):
    ## link x_range:
    x_range = None
    for field_layout in field_plots:
        wvfm_figure = field_layout.children[1].children[1].children[1]
        if x_range is None:
            x_range = wvfm_figure.x_range
        else:
            wvfm_figure.x_range = x_range

    Panel_Pulse = TabPanel(child=column(*field_plots), title=title)
    return Panel_Pulse  # TabPanel


def assemble_sequences(pulse_tabs: List):
    return Tabs(tabs=pulse_tabs)  # Tab


def format_spmod_data(spmod_ir, **assignments):
    d0 = {"uni": [], "chs": []}
    d1 = {"uni": [], "chs": []}
    scl = {"uni": [], "chs": []}

    locs, scales = spmod_ir._get_data(**assignments)
    name = None
    if str(spmod_ir) == "Uniform":
        name = "Uni"

        d0["uni"] += [name] * len(locs)
        d1["uni"] += list(locs)
        scl["uni"] += list(scales)
    else:
        name = "Channel"

        d0["chs"] += [name] * len(locs)
        d1["chs"] += list(locs)
        scl["chs"] += list(scales)

    return d0, d1, scl


def get_spmod_figure(spmod_ir, **assignments):
    d0, d1, scl = format_spmod_data(spmod_ir, **assignments)
    d0 = d0["uni"] + d0["chs"]
    d1 = d1["uni"] + d1["chs"]
    scl = scl["uni"] + scl["chs"]

    spmod_source = ColumnDataSource(
        data=dict(
            d0=d0,
            d1=d1,
            px=scl,
        )
    )
    cube = SpacialMod(spmod_source)
    return row(cube)


def get_waveform_figure(wvfm_ir, **assignments):
    # Varlist = []
    duration = float(wvfm_ir.duration(**assignments))
    times = np.linspace(0, duration, 1001)
    values = [wvfm_ir.__call__(time, **assignments) for time in times]
    fig = figure(
        sizing_mode="stretch_both",
        x_axis_label="Time (s)",
        y_axis_label="Waveform(t)",
        tools="hover",
    )
    fig.line(times, values)

    return fig


## =====================================================
# below are formatting IR data, and called by IR.
def format_field_data(field_ir, **assignments):
    # return should be
    # data: List[ColumnDataSources],
    # List[str]:ch_names,
    # spmod_source:ColumnDataSources

    out = {"uni": [], "chs": []}
    d0 = {"uni": [], "chs": []}
    d1 = {"uni": [], "chs": []}
    scl = {"uni": [], "chs": []}
    ch_names = {"uni": [], "chs": []}
    for spmod_ir, wvfm_ir in field_ir.value.items():
        ## deal with spmod:
        locs, scales = spmod_ir._get_data(**assignments)

        ## deal with wvfm:
        times, values = wvfm_ir._get_data(1000, **assignments)

        if str(spmod_ir) == "Uniform":
            name = "Uni[%d]" % (len(ch_names["uni"]))
            ch_names["uni"].append(name)

            lbl = [name] * len(times)
            out["uni"].append(
                ColumnDataSource(data=dict(wvfm_x=times, wvfm_y=values, lbl=lbl))
            )

            d0["uni"] += [name] * len(locs)
            d1["uni"] += list(locs)
            scl["uni"] += list(scales)
        else:
            name = "Ch[%d]" % (len(ch_names["chs"]))
            ch_names["chs"].append(name)

            lbl = [name] * len(times)
            out["chs"].append(
                ColumnDataSource(data=dict(wvfm_x=times, wvfm_y=values, lbl=lbl))
            )

            d0["chs"] += [name] * len(locs)
            d1["chs"] += list(locs)
            scl["chs"] += list(scales)

    ch_names = ch_names["uni"] + ch_names["chs"]
    out = out["uni"] + out["chs"]

    d0 = d0["uni"] + d0["chs"]
    d1 = d1["uni"] + d1["chs"]
    scl = scl["uni"] + scl["chs"]

    spmod_source = ColumnDataSource(
        data=dict(
            d0=d0,
            d1=d1,
            px=scl,
        )
    )

    return out, ch_names, spmod_source


def get_field_figure(ir_field, title, indicator, **assignments):
    dats, names, spinfo = format_field_data(ir_field, **assignments)
    if indicator is None:
        fig = Field_wvfm(
            colors=itertools.cycle(Dark2_5), data_sources=dats, ch_names=names
        )
    else:
        fig = Field_wvfm(
            colors=itertools.cycle(Dark2_5),
            data_sources=dats,
            ch_names=names,
            crx_hair_overlay=indicator,
        )
    cube = SpacialMod(spinfo)
    p1 = assemble_field(cube, fig, title)

    return p1


def get_pulse_panel(ir_pulse, title: str = None, **assignments):
    pulse_name, fields = ir_pulse._get_data(**assignments)
    if pulse_name is None:
        if title is not None:
            pulse_name = title
        else:
            pulse_name = "Pulse"

    shared_indicator = Span(dimension="height")
    pulse_figs = []
    for Field_name, field in fields.items():
        p = get_field_figure(field, str(Field_name), shared_indicator, **assignments)
        pulse_figs.append(p)
    p_all = assemble_pulse_panel(pulse_figs, pulse_name)
    return p_all


def get_pulse_figure(ir_pulse, title: str = None, **assginments):
    return Tabs(tabs=[get_pulse_panel(ir_pulse, title, **assginments)])


def get_sequence_figure(ir_seq, **assignments):
    seq_name, pulses = ir_seq._get_data(**assignments)

    pulse_all = []
    for lvl, pulse in pulses.items():
        if seq_name is None:
            p = get_pulse_panel(pulse, title=str(lvl), **assignments)
        else:
            p = get_pulse_panel(pulse, title=str(lvl) + f"({seq_name})", **assignments)
        pulse_all.append(p)

    Seq = assemble_sequences(pulse_all)
    return Seq


def get_ir_figure(ir, **assignments):
    # sequence, spmod and waveform does not need extra
    # pulse, field need extra arguments
    # so we handle separately
    from bloqade.ir.control.sequence import SequenceExpr
    from bloqade.ir.control.field import SpatialModulation
    from bloqade.ir.control.waveform import Waveform

    if isinstance(ir, SequenceExpr):
        return get_sequence_figure(ir, **assignments)
    elif isinstance(ir, SpatialModulation):
        return get_spmod_figure(ir, **assignments)
    elif isinstance(ir, Waveform):
        return get_waveform_figure(ir, **assignments)
    else:
        raise NotImplementedError(f"not supported IR for display, got {type(ir)}")
