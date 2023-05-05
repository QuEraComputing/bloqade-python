from pydantic.dataclasses import dataclass

max_print_depth = 10
unicode_enabled = True
# charset object, extracts away charset
@dataclass
class UnicodeCharSet:
    mid = "├"
    terminator = "└"
    skip = "│"
    dash = "─"
    trunc = "⋮"
    pair = " ⇒ "

@dataclass
class ASCIICharSet:
    mid = "+"
    terminator = "\\"
    skip = "|"
    dash = "--"
    trunc = "..."
    pair = " => "

@dataclass
class State:
    depth:int = 0
    prefix:str = ""
    last:bool = False

# all nodes should implement:
  # children method  -> either list or Dict
  # print_node method -> should just return str
  # print_annotation ->  should just return str

class Printer:

    def __init__(self, p):
        global unicode_enabled
        self.charset = UnicodeCharSet() if unicode_enabled else ASCIICharSet()
        self.state = State()
        self.p = p

    def should_print_annotation(self, children):
        if type(children) == list or type(children) == tuple: # or generator, not sure of equivalence in Python
            return False
        elif type(children) == dict:
            return True

    def print(self, node, cycle):
        
        # list of children
        children = node.children().copy()
        node_str = node.print_node()

        for i, line in enumerate(node_str.split('\n')):
            i != 0 and print(self.state.prefix)
            self.p.text(line)
            if not (self.state.last and len(children) == 0):
                self.p.text("\n")
        
        global max_print_depth
        if self.state.depth > max_print_depth or cycle: # need to set this variable dynamically
            self.p.text(self.p.charset.trunc)
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
                child_prefix += " " * (len(self.charset.skip) + len(self.charset.dash) + 1)

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

            if this_print_annotation and annotation is not None :
                """
                # object defines a print_annotation method which calls printstyled (in python we'll just let it be print, or it can just return a string for now)
                # keep in mind, doesn't even need the node as an argument, could just take the annotation
                key_str = sprint(Tree.print_annotation, node, annotation) 
                # then print the annotation itself
                print_annotation(node, annotation) # goes straight to printstyled (although node doesn't even need to be called, just annotation), should be defined within method?
                """
                self.p.text(annotation) # should just a return a string for now, otherwise have to redirect standard output
                self.p.text(self.charset.pair)
                child_prefix += " "*(len(annotation) + len(self.charset.pair))
            
            self.state.depth += 1
            parent_last = self.state.last
            self.state.last = is_last_leaf_child
            parent_prefix = self.state.prefix
            self.state.prefix = child_prefix

            if type(child) != str:
                self.print(child, cycle)
            else:
                self.p.text(child)
                self.p.text("\n")

            self.state.depth -= 1
            self.state.prefix = parent_prefix
            self.state.last = parent_last