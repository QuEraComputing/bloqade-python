from pydantic.dataclasses import dataclass
# charset object, extracts away charset
@dataclass(frozen=True)
class CharSet:
    mid = "├"
    terminator = "└"
    skip = "│"
    dash = "─"
    trunc = "⋮"
    pair = " ⇒ "

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

    def __init__(self, charset, max_depth, state, p):
        self.charset = charset
        self.max_depth = max_depth
        self.state = state
        self.p = p

    def should_print_annotation(self, children):
        if type(children) == list or type(children) == tuple: # or generator, not sure of equivalence in Python
            return False
        elif type(children) == dict:
            return True

    def print(self, node):
        
        # list of children
        children = node.children()
        node_str = node.print_node()

        for i, line in enumerate(node_str.split('\n')):
            i != 0 and print(self.state.prefix)
            self.p.text(line)
            if not (self.state.last and len(children) == 0):
                self.p.text("\n")
        
        if self.state.depth > self.max_depth:
            print(self.p.charset.trunc)
            print("\n")
            return

        this_print_annotation = self.should_print_annotation(children)

        """
            if a dictionary is encountered, 
            can convert the key-value pairs into a list of tuples

            s = Iterators.Stateful(
                this_print_annotation ? pairs(children) : children
            )
        """
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

            if this_print_annotation:
                """
                # object defines a print_annotation method which calls printstyled (in python we'll just let it be print, or it can just return a string for now)
                # keep in mind, doesn't even need the node as an argument, could just take the annotation
                key_str = sprint(Tree.print_annotation, node, annotation) 
                # then print the annotation itself
                print_annotation(node, annotation) # goes straight to printstyled (although node doesn't even need to be called, just annotation), should be defined within method?
                """
                key_str = node.print_annotation(annotation) # should just a return a string for now, otherwise have to redirect standard output
                self.p.text(key_str)
                self.p.text(self.charset.pair)
                child_prefix += " "*(len(key_str) + len(self.charset.pair))
            
            self.state.depth += 1
            parent_last = self.state.last
            self.state.last = is_last_leaf_child
            parent_prefix = self.state.prefix
            self.state.prefix = child_prefix
            self.print(child)
            self.state.depth -= 1
            self.state.prefix = parent_prefix
            self.state.last = parent_last