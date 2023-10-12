# use .__bases__ to get parents
from treelib import Tree

def inheritance_tree(node):
    stack = []
    stack.append(node)
    discovered = set()
    tree = Tree()
    
    while len(stack) != 0:
        node = stack.pop()
        tree.parent(node.__name__, node.__bases__[0].__name__)
        print(node)
        if node not in discovered:
            discovered.add(node)
            for neighbour in node.__bases__:
                if neighbour is not object:
                    stack.append(neighbour)


    return tree

