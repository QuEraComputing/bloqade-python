from bloqade.visualization.ir_visualize import (
    mock_data,
    Field_wvfm,
    SpacialMod,
    assemble_field,
    assemble_pulse_panel,
    assemble_sequences,
    mock_register,
)
import itertools
from bokeh import Dark2_5
from bokeh.model import Span
from bokeh.io import show
from bokeh.layouts import row


def test_mock_data():
    shared_indicator = Span(dimension="height")

    ## Rydberg:
    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p1 = assemble_field(cube, fig, "Detuning Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p2 = assemble_field(cube, fig, "Rabi amp Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p3 = assemble_field(cube, fig, "Rabi phase Fields")

    Panel_Pulse1 = assemble_pulse_panel([p1, p2, p3], "Rydberg")

    shared_indicator = Span(dimension="height")

    ## Hyperfine:
    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p1 = assemble_field(cube, fig, "Detuning Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p2 = assemble_field(cube, fig, "Rabi amp Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p3 = assemble_field(cube, fig, "Rabi phase Fields")

    Panel_Pulse2 = assemble_pulse_panel([p1, p2, p3], "Hyperfine")

    Seq = assemble_sequences([Panel_Pulse1, Panel_Pulse2])

    show(row(Seq, mock_register()))
