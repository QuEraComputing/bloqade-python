from bokeh.plotting import figure, show
from bokeh.layouts import column
from bokeh.models import Dropdown  # , CustomJS
from bokeh.models import (
    ColumnDataSource,
)

# from bokeh.models import Tabs, TabPanel, HoverTool, Div, CrosshairTool, Span
# from bokeh.palettes import Dark2_5

# import itertools
# import numpy as np
# from typing import List


## =====================================================
# below are formatting IR data, and called by IR.


def format_report_data(report, **assignments):
    # return should be
    # data: List[ColumnDataSources],
    # List[str]:ch_names,
    # spmod_source:ColumnDataSources

    task_tid = report.dataframe.index.get_level_values("task_number").unique()
    task_tid = list(task_tid)

    counts = report.counts

    assert len(task_tid) == len(counts)

    cnt_sources = []
    for i, cnt_data in enumerate(counts):
        bitstrings = cnt_data.keys()
        cnts = cnt_data.values()
        tid = [i] * len(cnts)
        src = ColumnDataSource(
            data=dict(
                tid=tid,
                bitstrings=bitstrings,
                cnts=cnts,
            )
        )
        cnt_sources.append(src)

    return cnt_sources


def mock_data():
    cnt_sources = []

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
    return cnt_sources


def counts_histogram(cnt_sources):
    menu = [(f"task {cnt}", f"{cnt}") for cnt in range(len(cnt_sources))]
    dropdown = Dropdown(label="Tasks", button_type="warning", menu=menu)

    p = figure(height=350, title="Counts", toolbar_location=None, tools="")

    for tsrc in cnt_sources:
        p.vbar(x="bitstrings", top="cnts", source=tsrc, width=0.9)

    p.xgrid.grid_line_color = None
    p.y_range.start = 0

    """
    dropdown.js_on_event("menu_item_click",
                         args=dict(glyphobj=glyph_obj, ),
                         code=CustomJS(code=
                                  "
                                    this.item, this.toString()
                                  "
                                 )
                        )
    """
    return column(dropdown, p)


if __name__ == "__main__":
    dat = mock_data()

    fig = counts_histogram(dat)

    show(fig)
