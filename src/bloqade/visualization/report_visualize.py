from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.models import (
    CustomJS,
    MultiChoice,
    Div,
    HoverTool,
    Range1d,
    ColorBar,
    TapTool,
)
from bokeh.models import ColumnDataSource, LinearColorMapper, Button, SVGIcon

# from bokeh.models import Tabs, TabPanel,, Div, CrosshairTool, Span
from bokeh.palettes import Dark2_5
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bloqade.task.base import Report

import math

# import itertools
import numpy as np
from decimal import Decimal

# from typing import List


## =====================================================
# below are formatting IR data, and called by IR.


def format_report_data(report: "Report"):
    # return should be
    # data: List[ColumnDataSources],
    # List[str]:ch_names,
    # spmod_source:ColumnDataSources

    task_tid = report.dataframe.index.get_level_values("task_number").unique()
    task_tid = list(task_tid)

    counts = report.counts
    ryds = report.rydberg_densities()

    print(len(task_tid))
    print(len(counts))

    assert len(task_tid) == len(counts)

    cnt_sources = []
    ryd_sources = []
    for i, cnt_data in enumerate(counts):
        # bitstrings = list(
        #    "\n".join(textwrap.wrap(bitstring, 32)) for bitstring in cnt_data.keys()
        # )
        bitstrings = cnt_data.keys()
        bit_id = [f"[{x}]" for x in range(len(bitstrings))]

        cnts = list(cnt_data.values())
        tid = [i] * len(cnts)
        src = ColumnDataSource(
            data=dict(tid=tid, bitstrings=bitstrings, cnts=cnts, bit_id=bit_id)
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

    return cnt_sources, ryd_sources, report.metas, report.geos, report.name


def mock_data():
    import bloqade.task as tks

    cnt_sources = []
    ryd_sources = []
    metas = []
    geos = []

    # ===============================
    bitstrings = ["0010", "1101", "1111"]
    cnts = [4, 7, 5]
    tid = [0] * len(cnts)
    bit_id = [f"[{x}]" for x in range(len(bitstrings))]
    src = ColumnDataSource(
        data=dict(tid=tid, bitstrings=bitstrings, cnts=cnts, bit_id=bit_id)
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
    geos.append(
        tks.base.Geometry(
            sites=[
                (0.0e-6, 0.0e-6),
                (0.0e-6, 0.5e-6),
                (0.5e-6, 0.3e-6),
                (0.6e-6, 0.7e-6),
            ],
            filling=[1, 1, 1, 0],
        )
    )

    # ===============================
    bitstrings = ["0101", "1101", "1110", "1111"]
    cnts = [4, 7, 5, 10]
    tid = [1] * len(cnts)
    bit_id = [f"[{x}]" for x in range(len(bitstrings))]
    src = ColumnDataSource(
        data=dict(tid=tid, bitstrings=bitstrings, cnts=cnts, bit_id=bit_id)
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
    geos.append(
        tks.base.Geometry(
            sites=[
                (0.0e-6, 0.1e-6),
                (0.66e-6, 0.5e-6),
                (0.3e-6, 0.3e-6),
                (0.5e-6, 0.7e-6),
            ],
            filling=[1, 0, 1, 0],
        )
    )

    return cnt_sources, ryd_sources, metas, geos, "Mock"


def plot_register_ryd_dense(geo, ryds):
    """obtain a figure object from the atom arrangement."""
    xs_filled, ys_filled, labels_filled, density_filled = [], [], [], []
    xs_vacant, ys_vacant, labels_vacant, density_vacant = [], [], [], []
    x_min = np.inf
    x_max = -np.inf
    y_min = np.inf
    y_max = -np.inf
    for idx, location_info in enumerate(zip(geo.sites, geo.filling, ryds)):
        (x, y), filling, density = location_info
        x = float(Decimal(str(x)) * Decimal("1e6"))  # convert to um
        y = float(Decimal(str(y)) * Decimal("1e6"))  # convert to um
        x_min = min(x, x_min)
        y_min = min(y, y_min)
        x_max = max(x, x_max)
        y_max = max(y, y_max)
        if filling:
            xs_filled.append(x)
            ys_filled.append(y)
            labels_filled.append(idx)
            density_filled.append(density)
        else:
            xs_vacant.append(x)
            ys_vacant.append(y)
            labels_vacant.append(idx)
            density_vacant.append(density)

    if len(geo.sites) > 0:
        length_scale = max(y_max - y_min, x_max - x_min, 1)
    else:
        length_scale = 1

    source_filled = ColumnDataSource(
        data=dict(
            _x=xs_filled, _y=ys_filled, _labels=labels_filled, _ryd=density_filled
        )
    )
    source_vacant = ColumnDataSource(
        data=dict(
            _x=xs_vacant, _y=ys_vacant, _labels=labels_vacant, _ryd=density_vacant
        )
    )

    hover = HoverTool()
    hover.tooltips = [
        ("(x,y)", "(@_x, @_y)"),
        ("index: ", "@_labels"),
        ("ryd density: ", "@_ryd"),
    ]

    color_mapper = LinearColorMapper(palette="Magma256", low=min(ryds), high=max(ryds))

    # specify that we want to map the colors to the y values,
    # this could be replaced with a list of colors
    ##p.scatter(x,y,color={'field': 'y', 'transform': color_mapper})

    ## remove box_zoom since we don't want to change the scale

    p = figure(
        width=500,
        height=400,
        tools="wheel_zoom,reset, undo, redo, pan",
        toolbar_location="above",
        title="rydberg density",
    )
    p.x_range = Range1d(x_min - 1, x_min + length_scale + 1)
    p.y_range = Range1d(y_min - 1, y_min + length_scale + 1)

    p.circle(
        "_x",
        "_y",
        source=source_filled,
        radius=0.035 * length_scale,
        fill_alpha=1,
        line_color="black",
        color={"field": "_ryd", "transform": color_mapper},
    )
    p.circle(
        "_x",
        "_y",
        source=source_vacant,
        radius=0.035 * length_scale,
        fill_alpha=1,
        # color="grey",
        line_color="black",
        color={"field": "_ryd", "transform": color_mapper},
        line_width=0.2 * length_scale,
    )

    color_bar = ColorBar(
        color_mapper=color_mapper,
        label_standoff=12,
        border_line_color=None,
        location=(0, 0),
    )

    p.xaxis.axis_label = "(um)"
    p.add_layout(color_bar, "right")
    p.add_tools(hover)

    return p


def plot_register_bits(geo):
    """obtain a figure object from the atom arrangement."""
    # xs_filled, ys_filled, labels_filled, density_filled = [], [], [], []
    # xs_vacant, ys_vacant, labels_vacant, density_vacant = [], [], [], []
    xs = []
    ys = []
    bits = []
    labels = []

    x_min = np.inf
    x_max = -np.inf
    y_min = np.inf
    y_max = -np.inf
    for idx, location_info in enumerate(zip(geo.sites, geo.filling)):
        (x, y), filling = location_info
        x = float(Decimal(str(x)) * Decimal("1e6"))  # convert to um
        y = float(Decimal(str(y)) * Decimal("1e6"))  # convert to um
        x_min = min(x, x_min)
        y_min = min(y, y_min)
        x_max = max(x, x_max)
        y_max = max(y, y_max)

        xs.append(x)
        ys.append(y)
        bits.append(0)
        labels.append(idx)

    if len(geo.sites) > 0:
        length_scale = max(y_max - y_min, x_max - x_min, 1)
    else:
        length_scale = 1

    source = ColumnDataSource(data=dict(_x=xs, _y=ys, _bits=bits, _labels=labels))

    hover = HoverTool()
    hover.tooltips = [
        ("(x,y)", "(@_x, @_y)"),
        ("index: ", "@_labels"),
        ("state: ", "@_bits"),
    ]

    color_mapper = LinearColorMapper(palette="Magma256", low=0, high=1)

    # specify that we want to map the colors to the y values,
    # this could be replaced with a list of colors
    ##p.scatter(x,y,color={'field': 'y', 'transform': color_mapper})

    ## remove box_zoom since we don't want to change the scale

    p = figure(
        width=400,
        height=400,
        tools="wheel_zoom,reset, undo, redo, pan",
        toolbar_location="above",
        title="reg state",
    )
    p.x_range = Range1d(x_min - 1, x_min + length_scale + 1)
    p.y_range = Range1d(y_min - 1, y_min + length_scale + 1)

    p.circle(
        "_x",
        "_y",
        source=source,
        radius=0.035 * length_scale,
        fill_alpha=1,
        line_color="black",
        color={"field": "_bits", "transform": color_mapper},
        name="reg",
    )

    p.xaxis.axis_label = "(um)"
    p.add_tools(hover)

    return p


def report_visual(cnt_sources, ryd_sources, metas, geos, name):
    options = [f"task {cnt}" for cnt in range(len(cnt_sources))]

    figs = []
    # select = Select(title="Select Task", options=[])
    multi_choice = MultiChoice(options=[])

    if len(options):
        color1 = Dark2_5[1]
        # color2 = Dark2_5[1]
        for taskname, tsrc, trydsrc, meta, geo in zip(
            options, cnt_sources, ryd_sources, metas, geos
        ):
            content = "<p> Assignments: </p>"
            for var, num in meta.items():
                content += f"<p>{var} = {num}</p>"

            div = Div(
                text=content, width=100, height=400, styles={"overflow-y": "scroll"}
            )

            xrng = [list(int(i) for i in x) for x in tsrc.data["bitstrings"]]

            print(xrng)

            p = figure(
                x_range=tsrc.data["bit_id"],
                height=400,
                width=400,
                title=f"{taskname}",
                # toolbar_location=None,
                tools="xwheel_zoom,reset, box_zoom, xpan",
            )
            bar_rend = p.vbar(
                x="bit_id", top="cnts", source=tsrc, width=0.9, color=color1
            )

            p.xgrid.grid_line_color = None
            p.xaxis.major_label_orientation = math.pi / 4
            p.y_range.start = 0
            p.yaxis.axis_label = "Counts"

            hov_tool = HoverTool()
            hov_tool.tooltips = [
                ("counts: ", "@cnts"),
                # ("bitstrings:\n", "@bitstrings"),
            ]
            p.add_tools(hov_tool)

            tap = TapTool(renderers=[bar_rend])
            p.add_tools(tap)
            p.toolbar.active_tap = tap

            preg = plot_register_bits(geo)
            # get render obj:
            reg_obj = None
            for rd in preg.renderers:
                if rd.name == "reg":
                    reg_obj = rd
                    break

            cb = CustomJS(
                args=dict(
                    tsrc=tsrc,
                    xrng=xrng,
                    bitsrc=reg_obj.data_source,
                    reg_obj=reg_obj,
                    preg=preg,
                ),
                code="""
                            var sel_bar_i = tsrc.selected.indices[0];
                            bitsrc.data['_bits'] = xrng[sel_bar_i];
                            preg.title.text = "reg state: [" + sel_bar_i + "]";
                            bitsrc.change.emit();
                            reg_obj.change.emit();
                            preg.change.emit();
                          """,
            )
            tsrc.selected.js_on_change("indices", cb)

            # pryd = figure(
            #    x_range=trydsrc.data["sites"],
            #    height=400,
            #    width=300,
            #    # toolbar_location=None,
            #    tools="xwheel_zoom,reset,box_zoom,xpan",
            # )

            # pryd.vbar(x="sites", top="ryds", source=trydsrc, width=0.5, color=color2)

            # pryd.xgrid.grid_line_color = None
            # pryd.y_range.start = 0
            # pryd.yaxis.axis_label = "Rydberg density"
            # pryd.xaxis.major_label_orientation = math.pi / 4
            # pryd.xaxis.axis_label = "site"

            # hov_tool = HoverTool()
            # hov_tool.tooltips = [("density: ", "@ryds")]
            # pryd.add_tools(hov_tool)

            # pgeo = plot_register(geo)
            # print(geo,  trydsrc.data["ryds"])
            pgeo = plot_register_ryd_dense(geo, trydsrc.data["ryds"])

            figs.append(row(div, p, preg, pgeo, name=taskname))
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

    # headline = row(Div(text="Report: " + name), bt)
    headline = Div(text="Report: " + name)

    bt = Button(label="Bloqade", icon=SVGIcon(svg=bloqadeICON()))
    bt.js_on_click(CustomJS(args=dict(url="about:blank"), code="window.open(url)"))

    bt2 = Button(label="QuEra", icon=SVGIcon(svg=queraICON()))
    bt2.js_on_click(
        CustomJS(args=dict(url="https://www.quera.com/"), code="window.open(url)")
    )

    return column(column(headline, row(bt, bt2)), column(multi_choice, column(*figs)))


def queraICON():
    return """
        <svg
    id="Layer_2"
    viewBox="0 0 154.96999 188.87825"
    version="1.1"
    sodipodi:docname="logo black.svg"
    width="154.96999"
    height="188.87825"
    inkscape:export-filename="QElogo.svg"
    inkscape:export-xdpi="96"
    inkscape:export-ydpi="96"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:svg="http://www.w3.org/2000/svg">
    <defs
        id="defs98" />
    <sodipodi:namedview
        id="namedview98"
        pagecolor="#ffffff"
        bordercolor="#000000"
        borderopacity="0.25"
        inkscape:showpageshadow="2"
        inkscape:pageopacity="0.0"
        inkscape:pagecheckerboard="0"
        inkscape:deskcolor="#d1d1d1" />
    <g
        id="g98"
        transform="translate(-90.150002,-1.4817416)">
        <circle
        cx="154.87"
        cy="178.75"
        r="11.61"
        id="circle7" />
        <circle
        cx="-177.98538"
        cy="126.21368"
        r="11.61"
        transform="rotate(-89.82)"
        id="circle8" />
        <circle
        cx="184.17"
        cy="178.75"
        r="11.61"
        id="circle9" />
        <circle
        cx="154.87"
        cy="13.46"
        r="11.61"
        id="circle10" />
        <circle
        cx="-12.696921"
        cy="125.69522"
        r="11.61"
        transform="rotate(-89.82)"
        id="circle11" />
        <circle
        cx="184.17"
        cy="13.46"
        r="11.61"
        id="circle12" />
        <circle
        cx="101.76"
        cy="159.53"
        r="11.61"
        id="circle13" />
        <circle
        cx="101.76"
        cy="126.13"
        r="11.61"
        id="circle14" />
        <circle
        cx="101.76"
        cy="95.919998"
        r="11.61"
        id="circle15" />
        <circle
        cx="101.76"
        cy="65.699997"
        r="11.61"
        id="circle16" />
        <circle
        cx="101.76"
        cy="35.490002"
        r="11.61"
        id="circle17" />
        <circle
        cx="154.87"
        cy="121.1"
        r="11.61"
        id="circle86" />
        <circle
        cx="181.08"
        cy="140.32001"
        r="11.61"
        id="circle87" />
        <circle
        cx="233.50999"
        cy="178.75"
        r="11.61"
        id="circle88" />
        <circle
        cx="207.42"
        cy="126.13"
        r="11.61"
        id="circle89" />
        <circle
        cx="207.42"
        cy="95.919998"
        r="11.61"
        id="circle90" />
        <circle
        cx="207.42"
        cy="65.699997"
        r="11.61"
        id="circle91" />
        <circle
        cx="207.42"
        cy="35.490002"
        r="11.61"
        id="circle92" />
        <circle
        cx="207.42"
        cy="159.53"
        r="11.61"
        id="circle93" />
        <circle
        cx="102.38"
        cy="126.13"
        r="11.61"
        id="circle94" />
        <circle
        cx="102.38"
        cy="95.919998"
        r="11.61"
        id="circle95" />
        <circle
        cx="102.38"
        cy="65.699997"
        r="11.61"
        id="circle96" />
        <circle
        cx="102.38"
        cy="35.490002"
        r="11.61"
        id="circle97" />
        <circle
        cx="102.38"
        cy="159.53"
        r="11.61"
        id="circle98" />
    </g>
    </svg>
    """


def bloqadeICON():
    return """
    <!-- Generator: Adobe Illustrator 27.0.0, SVG Export Plug-In .
        SVG Version: 6.00 Build 0)  -->

    <svg
    version="1.1"
    id="Layer_1"
    x="0px"
    y="0px"
    viewBox="0 0 120 125"
    xml:space="preserve"
    sodipodi:docname="logo.svg"
    width="120"
    height="125"
    inkscape:version="1.3 (0e150ed, 2023-07-21)"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:svg="http://www.w3.org/2000/svg"><defs
    id="defs16"><radialGradient
        id="SVGID_1_"
        cx="284.23792"
        cy="40.978001"
        r="70.431198"
        gradientUnits="userSpaceOnUse">&#10;				<stop
    offset="0"
    style="stop-color:#FFFFFF"
    id="stop7" />&#10;				<stop
    offset="0.1264"
    style="stop-color:#FBFAFF"
    id="stop8" />&#10;				<stop
    offset="0.2679"
    style="stop-color:#F1EDFF"
    id="stop9" />&#10;				<stop
    offset="0.4168"
    style="stop-color:#E0D6FF"
    id="stop10" />&#10;				<stop
    offset="0.5707"
    style="stop-color:#C7B7FF"
    id="stop11" />&#10;				<stop
    offset="0.7287"
    style="stop-color:#A88FFF"
    id="stop12" />&#10;				<stop
    offset="0.8875"
    style="stop-color:#825EFF"
    id="stop13" />&#10;				<stop
    offset="1"
    style="stop-color:#6437FF"
    id="stop14" />&#10;			</radialGradient></defs><sodipodi:namedview
    id="namedview16"
    pagecolor="#ffffff"
    bordercolor="#000000"
    borderopacity="0.25"
    inkscape:showpageshadow="2"
    inkscape:pageopacity="0.0"
    inkscape:pagecheckerboard="0"
    inkscape:deskcolor="#d1d1d1"
    inkscape:zoom="1.3545752"
    inkscape:cx="308.95296"
    inkscape:cy="72.347407"
    inkscape:window-width="1456"
    inkscape:window-height="803"
    inkscape:window-x="260"
    inkscape:window-y="138"
    inkscape:window-maximized="0"
    inkscape:current-layer="Layer_1" />&#10;<style
    type="text/css"
    id="style1">&#10;	.st0{fill:url(#SVGID_1_);}&#10;</style>&#10;&#10;<g
    id="g14"
    transform="matrix(0.97296819,0,0,1,-234.63028,-11.63275)">&#10;
    <path
    d="m 356,136.42 -15.67,-13.98 c -9.94,7.75 -22.57,12.47 -37.06,
    12.47 -35.88,0 -59.97,-28.13 -59.97,
    -60.64 v -0.34 c 0,-32.51 24.42,-60.98 60.3,
    -60.98 35.88,0 59.97,28.13 59.97,60.64 v 0.34 c 0,
    14.66 -5.22,28.64 -13.98,39.42 l 15.5,13.14 z m -25.1,
    -22.57 -22.07,-18.87 8.93,-9.94 22.07,20.04 c 6.4,
    -8.42 9.94,-19.03 9.94,-30.82 v -0.34 c 0,-26.78 -19.54,
    -48.68 -46.49,-48.68 -26.95,0 -46.15,
    21.56 -46.15,48.34 v 0.34 c 0,26.79 19.54,48.68 46.49,
    48.68 10.44,0 19.87,-3.19 27.28,-8.75 z"
    id="path7" />&#10;			<radialGradient
    id="radialGradient16"
    cx="284.23792"
    cy="40.978001"
    r="70.431198"
    gradientUnits="userSpaceOnUse">&#10;				<stop
    offset="0"
    style="stop-color:#FFFFFF"
    id="stop1" />&#10;				<stop
    offset="0.1264"
    style="stop-color:#FBFAFF"
    id="stop2" />&#10;				<stop
    offset="0.2679"
    style="stop-color:#F1EDFF"
    id="stop3" />&#10;				<stop
    offset="0.4168"
    style="stop-color:#E0D6FF"
    id="stop4" />&#10;				<stop
    offset="0.5707"
    style="stop-color:#C7B7FF"
    id="stop5" />&#10;				<stop
    offset="0.7287"
    style="stop-color:#A88FFF"
    id="stop6" />&#10;				<stop
    offset="0.8875"
    style="stop-color:#825EFF"
    id="stop15" />&#10;				<stop
    offset="1"
    style="stop-color:#6437FF"
    id="stop16" />&#10;			</radialGradient>&#10;			<circle
    class="st0"
    cx="303.78"
    cy="74.68"
    r="49.439999"
    id="circle14"
    style="fill:url(#SVGID_1_)" />&#10;		</g></svg>
    """
