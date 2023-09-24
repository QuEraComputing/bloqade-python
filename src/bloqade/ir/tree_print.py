# Ported from the Julia language AbstractTrees.jl implementation: https://github.com/JuliaCollections/AbstractTrees.jl/blob/master/src/printing.jl

from pydantic.dataclasses import dataclass
import sys
import bloqade.ir as ir

# The maximum depth of the tree to print.
max_tree_depth = 10


unicode_enabled = sys.stdout.encoding.lower().startswith("utf")
color_enabled = ("ipykernel" in sys.modules) or sys.stdout.isatty


class KeyValuePair:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, KeyValuePair):
            return False

        return self.key == __value.key and self.value == __value.value

    def children(self):
        return {"key": self.key, "value": self.value}

    def print_node(self):
        return "KeyValuePair"


# charset object, extracts away charset
@dataclass
class UnicodeCharSet:
    mid = "├"
    terminator = "└"
    skip = "│"
    dash = "─"
    trunc = "⋮"
    pair = "⇒ "


@dataclass
class ASCIICharSet:
    mid = "+"
    terminator = "\\"
    skip = "|"
    dash = "--"
    trunc = "..."
    pair = "=> "


@dataclass
class State:
    depth: int = 0
    prefix: str = ""
    last: bool = False


@dataclass
class ColorCode:
    CEND = "\33[0m"
    CBOLD = "\33[1m"
    CITALIC = "\33[3m"
    CURL = "\33[4m"
    CBLINK = "\33[5m"
    CBLINK2 = "\33[6m"
    CSELECTED = "\33[7m"

    CBLACK = "\33[30m"
    CRED = "\33[31m"
    CGREEN = "\33[32m"
    CYELLOW = "\33[33m"
    CBLUE = "\33[34m"
    CVIOLET = "\33[35m"
    CBEIGE = "\33[36m"
    CWHITE = "\33[37m"

    CBLACKBG = "\33[40m"
    CREDBG = "\33[41m"
    CGREENBG = "\33[42m"
    CYELLOWBG = "\33[43m"
    CBLUEBG = "\33[44m"
    CVIOLETBG = "\33[45m"
    CBEIGEBG = "\33[46m"
    CWHITEBG = "\33[47m"

    CGREY = "\33[90m"
    CRED2 = "\33[91m"
    CGREEN2 = "\33[92m"
    CYELLOW2 = "\33[93m"
    CBLUE2 = "\33[94m"
    CVIOLET2 = "\33[95m"
    CBEIGE2 = "\33[96m"
    CWHITE2 = "\33[97m"

    CGREYBG = "\33[100m"
    CREDBG2 = "\33[101m"
    CGREENBG2 = "\33[102m"
    CYELLOWBG2 = "\33[103m"
    CBLUEBG2 = "\33[104m"
    CVIOLETBG2 = "\33[105m"
    CBEIGEBG2 = "\33[106m"
    CWHITEBG2 = "\33[107m"

    def set_color(self, color, str):
        return color + str + self.CEND


# all nodes should implement:
# children method  -> either list or Dict
# print_node method -> should just return str
# print_annotation ->  should just return str


# p is needed for IPython Pretty printer or
# the following helper wrap, which collect the tree,
# and spit out the tree as raw string
class MockPrinter:
    def __init__(self):
        self.str_out = ""

    def text(self, segs: str):
        self.str_out += segs

    def get_value(self):
        return self.str_out

    # @property
    # def cycle_byterm(self):
    #    return int(os.get_terminal_size().columns / 10)


class Printer:
    def __init__(self, p=None):
        self.charset = UnicodeCharSet() if unicode_enabled else ASCIICharSet()
        self.colorcode = ColorCode()
        self.state = State()
        if p is None:
            self.p = MockPrinter()
        else:
            self.p = p
        self.max_tree_depth = max_tree_depth

    def should_print_annotation(self, children):
        if isinstance(
            children, (list, tuple)
        ):  # or generator, not sure of equivalence in Python
            return False
        elif isinstance(children, dict):
            return True

    def get_value(self):
        return self.p.get_value()

    def print(self, node, cycle=None):
        if cycle is None or isinstance(cycle, bool):
            cycle = max_tree_depth

        # list of children
        children = node.children().copy()
        node_str = node.print_node()

        if color_enabled:
            if isinstance(node, ir.Variable):
                node_str = self.colorcode.set_color(self.colorcode.CBLUE2, node_str)

        for i, line in enumerate(node_str.split("\n")):
            i != 0 and print(self.state.prefix)
            self.p.text(line)
            if not (self.state.last and len(children) == 0):
                self.p.text("\n")

        if (
            self.state.depth > self.max_tree_depth or self.state.depth > cycle
        ):  # need to set this variable dynamically
            self.p.text(self.charset.trunc)
            self.p.text("\n")
            return

        this_print_annotation = self.should_print_annotation(children)

        if this_print_annotation:
            children = list(children.items())

        while not len(children) == 0:
            child_prefix = self.state.prefix
            if this_print_annotation:
                annotation, child = children.pop(0)
            else:
                child = children.pop(0)
                annotation = None

            self.p.text(self.state.prefix)

            if len(children) == 0:
                self.p.text(self.charset.terminator)
                child_prefix += " " * (
                    len(self.charset.skip) + len(self.charset.dash) + 1
                )

                if self.state.depth > 0 and self.state.last:
                    is_last_leaf_child = True
                elif self.state.depth == 0:
                    is_last_leaf_child = True
                else:
                    is_last_leaf_child = False
            else:
                self.p.text(self.charset.mid)
                child_prefix += self.charset.skip + " " * (len(self.charset.dash) + 1)
                is_last_leaf_child = False

            self.p.text(self.charset.dash + " ")

            if this_print_annotation and annotation is not None:
                self.p.text(annotation)
                self.p.text("\n")
                self.p.text(child_prefix + self.charset.pair)
                child_prefix += " " * (len(self.charset.pair))

            self.state.depth += 1
            parent_last = self.state.last
            self.state.last = is_last_leaf_child
            parent_prefix = self.state.prefix
            self.state.prefix = child_prefix

            if not isinstance(child, str):
                self.print(child, cycle)
            else:
                self.p.text(child)
                self.p.text("\n")

            self.state.depth -= 1
            self.state.prefix = parent_prefix
            self.state.last = parent_last
