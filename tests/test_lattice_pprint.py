from bloqade import start, cast
from bloqade.ir.location import Square, Rectangular
import random
import numpy as np
import os
import bloqade.ir.tree_print as trp


trp.color_enabled = False


PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH = os.path.join(
    os.getcwd(), "tests/data/expected_pprint_output"
)


def test_list_of_locations_pprint():
    random.seed(1337)
    rand_positions = list(
        zip(
            [random.randint(0, 20) for _ in range(10)],
            [random.randint(0, 20) for _ in range(10)],
        )
    )

    list_of_locations_pprint_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH, "list_of_locations_pprint_output.txt"
    )
    list_of_locations_pprint_output = open(
        list_of_locations_pprint_output_path, "r"
    ).read()

    assert str(start.add_position(rand_positions)) == list_of_locations_pprint_output

    var1 = cast("var1")
    var2 = cast("var2")
    var3 = cast("var3")

    variable_list_of_locations = start.add_position([(var1, var2), (var3, 5), (0, 9)])

    assert str(variable_list_of_locations) == (
        "AtomArrangement\n"
        "├─ Location: filled\n"
        "│  ├─ x\n"
        "│  │  ⇒ Variable: var1\n"
        "│  └─ y\n"
        "│     ⇒ Variable: var2\n"
        "├─ Location: filled\n"
        "│  ├─ x\n"
        "│  │  ⇒ Variable: var3\n"
        "│  └─ y\n"
        "│     ⇒ Literal: 5\n"
        "└─ Location: filled\n"
        "   ├─ x\n"
        "   │  ⇒ Literal: 0\n"
        "   └─ y\n"
        "      ⇒ Literal: 9"
    )


def test_square_pprint():
    # full
    square_pprint_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH, "square_pprint_output.txt"
    )
    square_pprint_output = open(square_pprint_output_path, "r").read()

    assert str(Square(7)) == square_pprint_output

    # apply defect count
    square_pprint_defect_count_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH,
        "square_pprint_defect_count_output.txt",
    )
    square_pprint_defect_count_output = open(
        square_pprint_defect_count_output_path, "r"
    ).read()
    assert (
        str(Square(7).apply_defect_count(21, np.random.default_rng(1337)))
        == square_pprint_defect_count_output
    )

    # apply defect density
    square_pprint_defect_density_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH,
        "square_pprint_defect_density_output.txt",
    )
    square_pprint_defect_density_output = open(
        square_pprint_defect_density_output_path, "r"
    ).read()

    assert (
        str(Square(7).apply_defect_density(0.5, np.random.default_rng(1337)))
        == square_pprint_defect_density_output
    )

    # apply variable for lattice
    square_pprint_var_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH, "square_pprint_var_output.txt"
    )
    square_pprint_var_output = open(square_pprint_var_output_path, "r").read()

    bl = cast("bl")
    assert str(Square(7, lattice_spacing=bl)) == square_pprint_var_output


def test_rectangular_pprint():
    rectangular_pprint_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH, "rectangular_pprint_output.txt"
    )
    rectangular_pprint_output = open(rectangular_pprint_output_path, "r").read()

    assert str(Rectangular(7, 5)) == rectangular_pprint_output

    rectangular_pprint_defect_count_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH,
        "rectangular_pprint_defect_count_output.txt",
    )
    rectangular_pprint_defect_count_output = open(
        rectangular_pprint_defect_count_output_path, "r"
    ).read()

    assert (
        str(Rectangular(7, 5).apply_defect_count(15, np.random.default_rng(1337)))
        == rectangular_pprint_defect_count_output
    )

    rectangular_pprint_defect_density_output_path = os.path.join(
        PROJECT_RELATIVE_PPRINT_TESTS_OUTPUT_PATH,
        "rectangular_pprint_defect_density_output.txt",
    )
    rectangular_pprint_defect_density_output = open(
        rectangular_pprint_defect_density_output_path, "r"
    ).read()

    assert (
        str(Rectangular(7, 5).apply_defect_density(0.5, np.random.default_rng(1337)))
        == rectangular_pprint_defect_density_output
    )
