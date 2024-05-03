from bokeh.models import (
    ColumnDataSource,
    Range1d,
    HoverTool,
    LinearColorMapper,
    Select,
    CustomJS,
)
from bokeh.layouts import column
from bokeh.plotting import figure
import numpy as np
from typing import List, Tuple


def assemble_atom_arrangement_panel(atom_arrangement_plots: List, keys: List[str]):

    out = column(*atom_arrangement_plots)

    # 0 is always the filling
    select = Select(title="display info", options=keys, value=keys[0])
    select.js_on_change(
        "value",
        CustomJS(
            args=dict(figs=out.children, options=select.options, nelem=len(keys)),
            code="""
                                    const val = this.value
                                    for(let i=0;i<nelem;i++){
                                        figs[i].visible=false;
                                        if(val==options[i]){
                                            figs[i].visible=true;
                                        }
                                    }
                                """,
        ),
    )

    return column(select, out)


def get_atom_arrangement_figure(
    atom_arng_ir,
    colors: Tuple[List[int], List[float]] = (),
    fig_kwargs=None,
    **assignments,
):
    import bloqade.ir.location as ir_loc

    if len(colors) == 0:
        color_sites, color_weights = [], []
    else:
        color_sites, color_weights = colors

    """obtain a figure object from the atom arrangement."""
    xs_filled, ys_filled, labels_filled, color_filled = [], [], [], []
    xs_vacant, ys_vacant, labels_vacant, color_vacant = [], [], [], []
    x_min = np.inf
    x_max = -np.inf
    y_min = np.inf
    y_max = -np.inf
    for idx, location_info in enumerate(atom_arng_ir.enumerate()):
        (x_var, y_var) = location_info.position
        (x, y) = (float(x_var(**assignments)), float(y_var(**assignments)))
        x_min = min(x, x_min)
        y_min = min(y, y_min)
        x_max = max(x, x_max)
        y_max = max(y, y_max)
        if location_info.filling is ir_loc.location.SiteFilling.filled:
            xs_filled.append(x)
            ys_filled.append(y)
            labels_filled.append(idx)

            if idx in color_sites:
                color_filled.append(color_weights[color_sites.index(idx)])
            else:
                color_filled.append(0)

        else:
            xs_vacant.append(x)
            ys_vacant.append(y)
            labels_vacant.append(idx)

            if idx in color_sites:
                color_vacant.append(color_weights[color_sites.index(idx)])
            else:
                color_vacant.append(0)

    if atom_arng_ir.n_atoms > 0:
        length_scale = max(y_max - y_min, x_max - x_min, 1)
    else:
        length_scale = 1

    source_filled = ColumnDataSource(
        data=dict(
            _x=xs_filled, _y=ys_filled, _labels=labels_filled, _colorwt=color_filled
        )
    )
    source_vacant = ColumnDataSource(
        data=dict(
            _x=xs_vacant, _y=ys_vacant, _labels=labels_vacant, _colorwt=color_vacant
        )
    )
    source_all = ColumnDataSource(
        data=dict(
            _x=xs_vacant + xs_filled,
            _y=ys_vacant + ys_filled,
            _labels=labels_vacant + labels_filled,
        )
    )

    ## remove box_zoom since we don't want to change the scale
    if fig_kwargs is None:
        fig_kwargs = {}

    p = figure(
        **fig_kwargs,
        width=400,
        height=400,
        tools="wheel_zoom,reset, undo, redo, pan",
        toolbar_location="above",
    )
    p.x_range = Range1d(x_min - 1, x_min + length_scale + 1)
    p.y_range = Range1d(y_min - 1, y_min + length_scale + 1)
    if len(colors) == 0:
        p.circle(
            "_x", "_y", source=source_filled, radius=0.015 * length_scale, fill_alpha=1
        )
        p.circle(
            "_x",
            "_y",
            source=source_vacant,
            radius=0.015 * length_scale,
            fill_alpha=0.25,
            color="grey",
            line_width=0.2 * length_scale,
        )
        hover = HoverTool()
        hover.tooltips = [
            ("(x,y)", "(@_x, @_y)"),
            ("index: ", "@_labels"),
        ]
    else:
        # high = max(color_weights)
        color_mapper = LinearColorMapper(palette="Magma256", low=0, high=1)
        p.circle(
            "_x",
            "_y",
            source=source_filled,
            radius=0.015 * length_scale,
            fill_alpha=1,
            color={"field": "_colorwt", "transform": color_mapper},
        )
        p.circle(
            "_x",
            "_y",
            source=source_vacant,
            radius=0.015 * length_scale,
            fill_alpha=0.25,
            color={"field": "_colorwt", "transform": color_mapper},
            line_width=0.2 * length_scale,
        )
        hover = HoverTool()
        hover.tooltips = [
            ("(x,y)", "(@_x, @_y)"),
            ("index: ", "@_labels"),
            ("weight:", "@_colorwt"),
        ]

    p.circle(
        "_x",
        "_y",
        source=source_all,
        radius=0,  # in the same unit as the data
        fill_alpha=0.5,
        line_width=0.15 * length_scale,
        visible=True,  # display by default
        name="Brad",
    )
    p.add_tools(hover)

    return p
