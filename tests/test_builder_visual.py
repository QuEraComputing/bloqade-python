from bloqade.ir.location import Square
import numpy as np
from decimal import Decimal
from bloqade.visualization import builder_figure
from bokeh.io import save


def test_builder_vis():
    program = (
        Square(3, lattice_spacing=1 / np.sqrt(Decimal(2)))
        .apply_defect_count(4)
        .scale(6.1)
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 0.5, 0.1], [-10, -10, "final_detuning", "final_detuning"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 0.5, 0.1], [0, 15, 15, 0])
        .batch_assign(final_detuning=np.linspace(0, 50, 51).tolist())
    )
    fig = builder_figure(program, 0)
    save(fig)
