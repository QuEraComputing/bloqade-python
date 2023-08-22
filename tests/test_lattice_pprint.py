from bloqade import start, cast
from bloqade.ir.location import Square, Rectangular
import random
import numpy as np
from pathlib import Path

PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH = (
    Path.cwd() / "tests/data/expected_pprint_output"
)


def test_list_of_locations_pprint():
    random.seed(1337)
    rand_positions = list(
        zip(
            [random.randint(0, 20) for _ in range(10)],
            [random.randint(0, 20) for _ in range(10)],
        )
    )
    list_of_locations_pprint_output = (
        (
            PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH
            / "list_of_locations_pprint_output.txt"
        )
        .open()
        .read()
    )

    assert repr(start.add_positions(rand_positions)) == list_of_locations_pprint_output

    var1 = cast("var1")
    var2 = cast("var2")
    var3 = cast("var3")

    assert repr(start.add_positions([(var1, var2), (var3, 5), (0, 9)])) == (
        "[LocationInfo(position=(var(var1), var(var2)), "
        "filling=<SiteFilling.filled: 1>), "
        "LocationInfo(position=(var(var3), 5), filling=<SiteFilling.filled: 1>), "
        "LocationInfo(position=(0, 9), filling=<SiteFilling.filled: 1>)]"
    )


def test_square_pprint():
    # full
    square_pprint_output = (
        (PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH / "square_pprint_output.txt")
        .open()
        .read()
    )
    assert repr(Square(7)) == square_pprint_output

    # apply defect count
    square_pprint_defect_count_output = (
        (
            PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH
            / "square_pprint_defect_count_output.txt"
        )
        .open()
        .read()
    )
    assert (
        repr(Square(7).apply_defect_count(21, np.random.default_rng(1337)))
        == square_pprint_defect_count_output
    )

    # apply defect density
    square_pprint_defect_density_output = (
        (
            PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH
            / "square_pprint_defect_density_output.txt"
        )
        .open()
        .read()
    )
    assert (
        repr(Square(7).apply_defect_density(0.5, np.random.default_rng(1337)))
        == square_pprint_defect_density_output
    )

    # apply variable for lattice
    square_pprint_var_output = (
        (PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH / "square_pprint_var_output.txt")
        .open()
        .read()
    )
    bl = cast("bl")
    assert repr(Square(7, bl)) == square_pprint_var_output


def test_rectangular_pprint():
    rectangular_pprint_output = (
        (PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH / "rectangular_pprint_output.txt")
        .open()
        .read()
    )
    assert repr(Rectangular(7, 5)) == rectangular_pprint_output

    rectangular_pprint_defect_count_output = (
        (
            PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH
            / "rectangular_pprint_defect_count_output.txt"
        )
        .open()
        .read()
    )
    assert (
        repr(Rectangular(7, 5).apply_defect_count(15, np.random.default_rng(1337)))
        == rectangular_pprint_defect_count_output
    )

    rectangular_pprint_defect_density_output = (
        (
            PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH
            / "rectangular_pprint_defect_density_output.txt"
        )
        .open()
        .read()
    )
    assert (
        repr(Rectangular(7, 5).apply_defect_density(0.5, np.random.default_rng(1337)))
        == rectangular_pprint_defect_density_output
    )

    x_spacing = cast("x_spacing")
    assert repr(Rectangular(7, 5, x_spacing)) == (
        "Rectangular(shape=(7, 5), "
        "lattice_spacing=var(x_spacing), "
        "ratio=(1.0 / var(x_spacing)))"
    )
