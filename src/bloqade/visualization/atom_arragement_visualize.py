from bokeh.models import (
    ColumnDataSource,
    Range1d,
    HoverTool,
)
from bokeh.plotting import figure
import numpy as np


def get_atom_arrangement_figure(atom_arng_ir, fig_kwargs=None, **assignments):
    import bloqade.ir.location as ir_loc

    """obtain a figure object from the atom arrangement."""
    xs_filled, ys_filled, labels_filled = [], [], []
    xs_vacant, ys_vacant, labels_vacant = [], [], []
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
        if location_info.filling is ir_loc.base.SiteFilling.filled:
            xs_filled.append(x)
            ys_filled.append(y)
            labels_filled.append(idx)
        else:
            xs_vacant.append(x)
            ys_vacant.append(y)
            labels_vacant.append(idx)

    if atom_arng_ir.n_atoms > 0:
        length_scale = max(y_max - y_min, x_max - x_min, 1)
    else:
        length_scale = 1

    source_filled = ColumnDataSource(
        data=dict(_x=xs_filled, _y=ys_filled, _labels=labels_filled)
    )
    source_vacant = ColumnDataSource(
        data=dict(_x=xs_vacant, _y=ys_vacant, _labels=labels_vacant)
    )
    source_all = ColumnDataSource(
        data=dict(
            _x=xs_vacant + xs_filled,
            _y=ys_vacant + ys_filled,
            _labels=labels_vacant + labels_filled,
        )
    )
    hover = HoverTool()
    hover.tooltips = [
        ("(x,y)", "(@_x, @_y)"),
        ("index: ", "@_labels"),
    ]

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
