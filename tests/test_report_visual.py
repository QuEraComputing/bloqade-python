from bloqade.visualization.report_visualize import mock_data, report_visual
from bokeh.io import save


def test_report_vis_mock():
    dat = mock_data()

    fig = report_visual(*dat)

    save(fig)
    # from bokeh.models import SVGIcon

    # p = figure(width=200, height=100, toolbar_location=None)
    # p.image_url(url="file:///./logo.png")
    # button = Button(label="", icon=SVGIcon(svg=bloqadeICON(), size=50))
    # show(button)
