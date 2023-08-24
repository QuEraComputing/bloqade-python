from bokeh.plotting import figure, show
from bokeh.layouts import column, row
from bokeh.models import CustomJS, MultiChoice, Div, HoverTool
from bokeh.models import (
    ColumnDataSource,
)

# from bokeh.models import Tabs, TabPanel,, Div, CrosshairTool, Span
from bokeh.palettes import Dark2_5
import math

# import itertools
# import numpy as np
# from typing import List


## =====================================================
# below are formatting IR data, and called by IR.


def format_report_data(report):
    # return should be
    # data: List[ColumnDataSources],
    # List[str]:ch_names,
    # spmod_source:ColumnDataSources

    task_tid = report.dataframe.index.get_level_values("task_number").unique()
    task_tid = list(task_tid)

    counts = report.counts
    ryds = report.rydberg_densities()
    assert len(task_tid) == len(counts)

    cnt_sources = []
    ryd_sources = []
    for i, cnt_data in enumerate(counts):
        bitstrings = list(cnt_data.keys())
        cnts = list(cnt_data.values())
        tid = [i] * len(cnts)
        src = ColumnDataSource(
            data=dict(
                tid=tid,
                bitstrings=bitstrings,
                cnts=cnts,
            )
        )

        rydens = list(ryds.iloc[i])
        tid = [i] * len(rydens)

        rsrc = ColumnDataSource(
            data=dict(
                tid=tid,
                sites=[f"{ds}" for ds in range(len(rydens))],
                ryds=rydens,
            )
        )
        cnt_sources.append(src)
        ryd_sources.append(rsrc)

    return cnt_sources, ryd_sources, report.metas, report.name


def mock_data():
    cnt_sources = []
    ryd_sources = []
    metas = []

    # ===============================
    bitstrings = ["0010", "1101", "1111"]
    cnts = [4, 7, 5]
    tid = [0] * len(cnts)
    src = ColumnDataSource(
        data=dict(
            tid=tid,
            bitstrings=bitstrings,
            cnts=cnts,
        )
    )
    cnt_sources.append(src)
    rsrc = ColumnDataSource(
        data=dict(
            tid=[0, 0, 0, 0],
            sites=["0", "1", "2", "3"],
            ryds=[0.55, 0.45, 0.2, 0.11],
        )
    )
    ryd_sources.append(rsrc)
    metas.append(dict(a=4, b=9, c=10))

    # ===============================
    bitstrings = ["0101", "1101", "1110", "1111"]
    cnts = [4, 7, 5, 10]
    tid = [1] * len(cnts)
    src = ColumnDataSource(
        data=dict(
            tid=tid,
            bitstrings=bitstrings,
            cnts=cnts,
        )
    )
    cnt_sources.append(src)
    rsrc = ColumnDataSource(
        data=dict(
            tid=[1, 1, 1, 1],
            sites=["0", "1", "2", "3"],
            ryds=[0.33, 0.67, 0.25, 0.34],
        )
    )
    ryd_sources.append(rsrc)
    metas.append(dict(a=10, b=9.44, c=10.3))

    return cnt_sources, ryd_sources, metas, "Mock"


def report_visual(cnt_sources, ryd_sources, metas, name):
    options = [f"task {cnt}" for cnt in range(len(cnt_sources))]

    figs = []
    # select = Select(title="Select Task", options=[])
    multi_choice = MultiChoice(options=[])

    if len(options):
        color1 = Dark2_5[0]
        color2 = Dark2_5[1]
        for taskname, tsrc, trydsrc, meta in zip(
            options, cnt_sources, ryd_sources, metas
        ):
            content = "<p> Assignments: </p>"
            for var, num in meta.items():
                content += f"<p>{var} = {num}</p>"

            div = Div(
                text=content, width=100, height=400, styles={"overflow-y": "scroll"}
            )

            p = figure(
                x_range=tsrc.data["bitstrings"],
                height=400,
                title=f"{taskname}",
                # toolbar_location=None,
                tools="xwheel_zoom,reset, box_zoom, xpan",
            )
            p.vbar(x="bitstrings", top="cnts", source=tsrc, width=0.9, color=color1)

            p.xgrid.grid_line_color = None
            p.xaxis.major_label_orientation = math.pi / 4
            p.y_range.start = 0
            p.yaxis.axis_label = "Counts"

            hov_tool = HoverTool()
            hov_tool.tooltips = [
                ("counts: ", "@cnts"),
                ("bitstrings:\n", "@bitstrings"),
            ]
            p.add_tools(hov_tool)

            pryd = figure(
                x_range=trydsrc.data["sites"],
                height=400,
                width=300,
                # toolbar_location=None,
                tools="xwheel_zoom,reset,box_zoom,xpan",
            )

            pryd.vbar(x="sites", top="ryds", source=trydsrc, width=0.5, color=color2)

            pryd.xgrid.grid_line_color = None
            pryd.y_range.start = 0
            pryd.yaxis.axis_label = "Rydberg density"
            pryd.xaxis.major_label_orientation = math.pi / 4
            pryd.xaxis.axis_label = "site"

            hov_tool = HoverTool()
            hov_tool.tooltips = [("density: ", "@ryds")]
            pryd.add_tools(hov_tool)

            figs.append(row(div, p, pryd, name=taskname))
            figs[-1].visible = False

        # Create a dropdown menu to select between the two graphs
        figs[0].visible = True
        multi_choice = MultiChoice(value=[options[0]], options=options)

        multi_choice.js_on_change(
            "value",
            CustomJS(
                args=dict(figs=figs, options=options, nelem=len(options)),
                code="""
                        const vals = this.value
                        for(let i=0;i<nelem;i++){
                            figs[i].visible=false;
                            for(let j=0;j<vals.length;j++){
                                if(vals[j]==options[i]){
                                    figs[i].visible=true;
                                    break;
                                }
                            }
                        }
                    """,
            ),
        )

    return column(Div(text="Report: " + name), column(multi_choice, column(*figs)))


if __name__ == "__main__":
    dat = mock_data()

    fig = report_visual(*dat)

    show(fig)
