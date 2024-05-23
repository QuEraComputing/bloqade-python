import bloqade


def test_global_treedepth():
    bloqade.ui.tree_depth(4)
    assert bloqade.ui.tree_depth() == 4
    bloqade.ui.tree_depth(10)
    assert bloqade.ui.tree_depth() == 10
