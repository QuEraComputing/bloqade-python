import bloqade


def test_global_treedepth():
    bloqade.tree_depth(4)
    assert bloqade.tree_depth() == 4
    bloqade.tree_depth(10)
    assert bloqade.tree_depth() == 10
