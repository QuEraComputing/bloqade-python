# use .__bases__ to get parents
from treelib import Tree

def superclass_tree(node):
    stack = []
    stack.append(node)
    discovered = set()

    tree = Tree()
    tree.create_node(node.__name__, node.__name__)

    while len(stack) != 0:
        node = stack.pop()
        print(node.__name__)
        if node not in discovered:
            discovered.add(node)
            for neighbour in node.__bases__:
                if neighbour is not object:
                    tree.create_node(neighbour, neighbour.__name__, parent=node)
                    stack.append(neighbour)


    return tree

# see the subclasses
def subclass_tree(node):
    stack = []
    stack.append(node)
    discovered = set()

    tree = Tree()
    tree.create_node(node.__name__, node.__name__)

    while len(stack) != 0:
        node = stack.pop()
        print(node)
        if node not in discovered:
            discovered.add(node)
            for neighbour in node.__subclasses__():
                if neighbour is not object:
                    tree.create_node(neighbour.__name__, neighbour.__name__, parent=node.__name__)
                    stack.append(neighbour)


    return tree

def nx_subclass_tree(node):
    stack = []
    traversal_list = []
    stack.append(node)
    discovered = set()

    while len(stack) != 0:
        node = stack.pop()
        print(node)
        if node not in discovered:
            discovered.add(node)
            for neighbour in node.__subclasses__():
                if neighbour not in discovered:
                    if neighbour is not object:
                        stack.append(neighbour)
                        traversal_list.append((node.__name__, neighbour.__name__, "grey"))
                        node_attrs = [attr for attr in dir(node) if '__' not in attr]
                        for node_attr in node_attrs:
                            traversal_list.append((node.__name__, node_attr, "red"))
                else:
                    # cycle detected
                    print(f"Cycle Detected: {node.__name__} -> {neighbour.__name__}")
                    traversal_list.append((node.__name__, neighbour.__name__, "grey"))

    return traversal_list

import networkx as nx 
import matplotlib.pyplot as plt
import pydot
from networkx.drawing.nx_pydot import graphviz_layout
import bloqade

traversed_nodes = nx_subclass_tree(bloqade.builder.base.Builder)
edges = []
colors = []
for (parent, child, color) in traversed_nodes:
    edges.append((parent, child))
    colors.append(color)

# list of tuples in format [(parent, child, color)]
# need to get the colors in their own list
G = nx.DiGraph()
G.add_edges_from(edges)
pos = graphviz_layout(G, prog='dot')
nx.draw(G, 
        pos, 
        edge_color = colors,
        with_labels=True, 
        font_size=8)
plt.show()