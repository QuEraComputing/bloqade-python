from dataclasses import dataclass
from typing import Optional, List
from .. import ir
from .base import Builder
from .coupling import Rydberg, Hyperfine
from .field import Detuning, RabiAmplitude, RabiPhase
from .spatial import SpatialModulation, Location, Uniform, Var, Scale


@dataclass
class BuilderNode:
    node: Builder
    next: Optional["BuilderNode"] = None

    def __repr__(self) -> str:
        return repr(self.node)


class BuilderStream:
    """Represents a stream of builder nodes."""

    def __init__(self, builder: Builder) -> None:
        self.head = self.build_nodes(builder)
        self.curr = self.head

    def read(self) -> BuilderNode | None:
        if self.curr is None:
            return None

        node = self.curr
        self.curr = self.curr.next
        return node

    def read_next(self, builder_types: List[type[Builder]]) -> BuilderNode | None:
        node = self.read()
        while node is not None:
            if type(node.node) in builder_types:
                return node
            node = self.read()
        return None

    def next_spatial(self) -> SpatialModulation | None:
        return self.read_next([Location, Uniform, Var])

    def eat_spatial(self):
        head = self.next_spatial()
        curr = head
        while curr is not None:
            if type(curr.node) not in [Location, Uniform, Var, Scale]:
                break
            curr = curr.next
        self.curr = curr
        return head

    def __iter__(self):
        return self

    def __next__(self):
        node = self.read()
        if node is None:
            raise StopIteration
        return node

    @staticmethod
    def build_nodes(ast: Builder) -> "BuilderNode":
        curr = ast
        node = None
        while curr is not None:
            next = curr
            curr = curr.__parent__
            node = BuilderNode(next, node)

        return node


class PulseCompiler:
    def __init__(self, ast: Builder) -> None:
        self.stream = BuilderStream(ast)

    def next_channel_pair(self):
        spatial = self.stream.eat_spatial()
        if type(spatial.node.__parent__) in [Detuning, RabiAmplitude, RabiPhase]:
            field = spatial.node.__parent__  # field is updated
            if type(field) in [RabiAmplitude, RabiPhase]:
                coupling = field.__parent__.__parent__  # skip Rabi
            else:
                coupling = field.__parent__

            # coupling not updated
            if type(coupling) not in [Rydberg, Hyperfine]:
                coupling = None
            return (coupling, field, spatial)
        else:  # only spatial is updated
            return (None, None, spatial)

    def read_waveform(self) -> "ir.Waveform":
        pass


# class BuilderVisitor:

#     def visit(self, ast: Builder):
#         name = 'visit_' + type(ast).__name__.lower()
#         if hasattr(self, name):
#             return getattr(self, name)(ast)
#         else:
#             raise NotImplementedError(f'No method {name} for {type(self).__name__}')
