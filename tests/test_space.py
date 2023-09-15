from bloqade.emulate.ir.space import Space
from bloqade.emulate.ir.atom_type import ThreeLevelAtom, TwoLevelAtom
from bloqade.emulate.ir.emulator import Register
import numpy as np


def test_two_level_space():
    positions = [(0, 0), (0, 1)]
    register = Register(TwoLevelAtom, positions, 0)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 4
    assert np.all(space.configurations == np.array([0, 1, 2, 3]))


def test_two_level_subspace():
    positions = [(0, 0), (0, 1)]
    register = Register(TwoLevelAtom, positions, 1.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 3
    assert np.all(space.configurations == np.array([0, 1, 2]))


def test_two_level_subspace_2():
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    register = Register(TwoLevelAtom, positions, np.sqrt(2) + 0.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 4
    assert space.size == 5
    assert np.all(space.configurations == np.array([0, 1, 2, 4, 8]))


def test_three_level_space():
    positions = [(0, 0), (0, 1)]
    register = Register(ThreeLevelAtom, positions, 0)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 9
    assert np.all(space.configurations == np.array([0, 1, 2, 3, 4, 5, 6, 7, 8]))


def test_three_level_subspace():
    positions = [(0, 0), (0, 1)]
    register = Register(ThreeLevelAtom, positions, 1.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 8
    assert np.all(space.configurations == np.array([0, 1, 2, 3, 4, 5, 6, 7]))


def test_three_level_subspace_2():
    positions = [(0, 0), (0.5, np.sqrt(3) / 2), (0, 1)]
    register = Register(ThreeLevelAtom, positions, 1.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 3
    assert space.size == 20
    assert np.all(
        space.configurations
        == np.array(
            [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 21, 22]
        )
    )


def test_two_level_integer_to_string():
    assert TwoLevelAtom.integer_to_string(0, 2) == "|gg>"
    assert TwoLevelAtom.integer_to_string(1, 2) == "|rg>"
    assert TwoLevelAtom.integer_to_string(2, 2) == "|gr>"
    assert TwoLevelAtom.integer_to_string(3, 2) == "|rr>"


def test_two_level_string_to_integer():
    assert TwoLevelAtom.string_to_integer("|gg>") == 0
    assert TwoLevelAtom.string_to_integer("|rg>") == 1
    assert TwoLevelAtom.string_to_integer("|gr>") == 2
    assert TwoLevelAtom.string_to_integer("|rr>") == 3


def test_three_level_integer_to_string():
    assert ThreeLevelAtom.integer_to_string(0, 2) == "|gg>"
    assert ThreeLevelAtom.integer_to_string(1, 2) == "|hg>"
    assert ThreeLevelAtom.integer_to_string(2, 2) == "|rg>"
    assert ThreeLevelAtom.integer_to_string(3, 2) == "|gh>"
    assert ThreeLevelAtom.integer_to_string(4, 2) == "|hh>"
    assert ThreeLevelAtom.integer_to_string(5, 2) == "|rh>"
    assert ThreeLevelAtom.integer_to_string(6, 2) == "|gr>"
    assert ThreeLevelAtom.integer_to_string(7, 2) == "|hr>"
    assert ThreeLevelAtom.integer_to_string(8, 2) == "|rr>"


def test_three_level_string_to_integer():
    assert ThreeLevelAtom.string_to_integer("|gg>") == 0
    assert ThreeLevelAtom.string_to_integer("|hg>") == 1
    assert ThreeLevelAtom.string_to_integer("|rg>") == 2
    assert ThreeLevelAtom.string_to_integer("|gh>") == 3
    assert ThreeLevelAtom.string_to_integer("|hh>") == 4
    assert ThreeLevelAtom.string_to_integer("|rh>") == 5
    assert ThreeLevelAtom.string_to_integer("|gr>") == 6
    assert ThreeLevelAtom.string_to_integer("|hr>") == 7
    assert ThreeLevelAtom.string_to_integer("|rr>") == 8


def test_two_level_swap_indices():
    positions = [(0, 0), (0, 1), (1, 0)]
    register = Register(TwoLevelAtom, positions, 0)
    space = Space.create(register)
    print(space)

    row_indices, col_indices = space.swap_state_at(0, 0, 1)

    row_indices_expected = slice(None, None, None)
    col_indices_expected = np.array([1, 0, 3, 2, 5, 4, 7, 6])

    assert row_indices == row_indices_expected
    assert np.all(col_indices == col_indices_expected)

    row_indices, col_indices = space.swap_state_at(1, 0, 1)

    row_indices_expected = slice(None, None, None)
    col_indices_expected = np.array([2, 3, 0, 1, 6, 7, 4, 5])

    assert row_indices == row_indices_expected
    assert np.all(col_indices == col_indices_expected)

    row_indices, col_indices = space.swap_state_at(2, 0, 1)

    row_indices_expected = slice(None, None, None)
    col_indices_expected = np.array([4, 5, 6, 7, 0, 1, 2, 3])

    assert row_indices == row_indices_expected
    assert np.all(col_indices == col_indices_expected)


def test_three_level_swap_indices():
    positions = [(0, 0), (0, 1)]
    register = Register(ThreeLevelAtom, positions, 0)
    space = Space.create(register)
    print(space)

    # 0. |gg>
    # 1. |hg>
    # 2. |rg>
    # 3. |gh>
    # 4. |hh>
    # 5. |rh>
    # 6. |gr>
    # 7. |hr>
    # 8. |rr>

    row_indices, col_indices = space.swap_state_at(0, 0, 1)

    row_indices_expected = np.array(
        [True, True, False, True, True, False, True, True, False]
    )
    col_indices_expected = np.array(
        [
            ThreeLevelAtom.string_to_integer("|hg>"),
            ThreeLevelAtom.string_to_integer("|gg>"),
            ThreeLevelAtom.string_to_integer("|hh>"),
            ThreeLevelAtom.string_to_integer("|gh>"),
            ThreeLevelAtom.string_to_integer("|hr>"),
            ThreeLevelAtom.string_to_integer("|gr>"),
        ]
    )

    assert np.all(row_indices == row_indices_expected)
    assert np.all(col_indices == col_indices_expected)

    # 0. |gg>
    # 1. |hg>
    # 2. |rg>
    # 3. |gh>
    # 4. |hh>
    # 5. |rh>
    # 6. |gr>
    # 7. |hr>
    # 8. |rr>

    row_indices, col_indices = space.swap_state_at(0, 1, 2)

    row_indices_expected = np.array(
        [False, True, True, False, True, True, False, True, True]
    )
    col_indices_expected = np.array(
        [
            ThreeLevelAtom.string_to_integer("|rg>"),
            ThreeLevelAtom.string_to_integer("|hg>"),
            ThreeLevelAtom.string_to_integer("|rh>"),
            ThreeLevelAtom.string_to_integer("|hh>"),
            ThreeLevelAtom.string_to_integer("|rr>"),
            ThreeLevelAtom.string_to_integer("|hr>"),
        ]
    )

    assert np.all(row_indices == row_indices_expected)
    assert np.all(col_indices == col_indices_expected)


test_three_level_swap_indices()
