from bokeh.plotting import figure, show
from bokeh.layouts import column, row
from bokeh.models import Select, CustomJS
from bokeh.models import (
    ColumnDataSource,
)

# from bokeh.models import Tabs, TabPanel, HoverTool, Div, CrosshairTool, Span
from bokeh.palettes import Dark2_5

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
                bits=["0", "1"],
                ryds=rydens,
            )
        )
        cnt_sources.append(src)
        ryd_sources.append(rsrc)

    return cnt_sources, ryd_sources


def mock_data():
    cnt_sources = []
    ryd_sources = []

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
            tid=[0, 0],
            bits=["0", "1"],
            ryds=[0.55, 0.45],
        )
    )
    ryd_sources.append(rsrc)

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
            tid=[1, 1],
            bits=["0", "1"],
            ryds=[0.33, 0.67],
        )
    )
    ryd_sources.append(rsrc)

    return cnt_sources, ryd_sources


def report_visual(cnt_sources, ryd_sources):
    options = [f"task {cnt}" for cnt in range(len(cnt_sources))]

    figs = []
    select = Select(title="Select Task", options=[])

    if len(options):
        color1 = Dark2_5[0]
        color2 = Dark2_5[1]
        for taskname, tsrc, trydsrc in zip(options, cnt_sources, ryd_sources):
            p = figure(
                x_range=tsrc.data["bitstrings"],
                height=400,
                title=f"{taskname}",
                toolbar_location=None,
                tools="",
            )
            p.vbar(x="bitstrings", top="cnts", source=tsrc, width=0.9, color=color1)

            p.xgrid.grid_line_color = None
            p.y_range.start = 0
            p.yaxis.axis_label = "Counts"

            pryd = figure(
                x_range=["0", "1"],
                height=400,
                width=200,
                toolbar_location=None,
                tools="",
            )

            pryd.vbar(x="bits", top="ryds", source=trydsrc, width=0.5, color=color2)

            pryd.xgrid.grid_line_color = None
            pryd.y_range.start = 0
            pryd.yaxis.axis_label = "Rydberg density"

            figs.append(row(p, pryd, name=taskname))

        # Create a dropdown menu to select between the two graphs
        select = Select(title="Select Task", options=["all"] + options, value="all")

        # Define a JavaScript callback
        callback = CustomJS(
            args=dict(figs=figs, nelem=len(options)),
            code="""
            var selected_value = cb_obj.value;
            if(selected_value==="all"){
                for(let i=0;i<nelem;i++){
                    figs[i].visible = true;
                }
            }else{
                for(let i=0;i<nelem;i++){
                    if(figs[i].name === selected_value){
                        figs[i].visible = true;
                    }else{
                        figs[i].visible = false;
                    }
                }
            }
        """,
        )

        select.js_on_change("value", callback)

    return column(select, column(*figs))


if __name__ == "__main__":
    dat = mock_data()

    fig = report_visual(*dat)

    show(fig)
