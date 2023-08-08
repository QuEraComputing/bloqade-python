from dataclasses import dataclass
from typing import Optional, List, Type
from .. import ir
from .base import Builder
from .coupling import Rydberg, Hyperfine
from .field import Detuning, RabiAmplitude, RabiPhase
from .spatial import Location, Uniform, Var, Scale
from .waveform import (
    WaveformPrimitive,
    Linear,
    Constant,
    Poly,
    PiecewiseConstant,
    PiecewiseLinear,
    Fn,
    Slice,
    Record,
)


@dataclass
class BuilderNode:
    node: Builder
    next: Optional["BuilderNode"] = None

    def __repr__(self) -> str:
        return repr(self.node)


@dataclass
class BuilderStream:
    """Represents a stream of builder nodes."""

    head: BuilderNode
    curr: Optional[BuilderNode] = None

    def copy(self) -> "BuilderStream":
        return BuilderStream(head=self.head, curr=self.curr)

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

    def eat(
        self, types: List[Type[Builder]], skips: List[Type[Builder]] | None = None
    ) -> BuilderNode:
        """Scan the stream until a node of type in `types` or `skips` is found.

        Args:
            types (List[Type[Builder]]): List of types to move the stream pointer to
            skips (List[Type[Builder]] | None, optional): List of types to end the
            stream scan

        Returns:
            BuilderNode: The beginning of the stream which matches a type in `types`.
        """
        head = self.read_next(types)
        curr = head
        while curr is not None:
            if type(curr.node) not in types:
                if skips and type(curr.node) not in skips:
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

    @staticmethod
    def create(builder: Builder) -> "BuilderStream":
        head = BuilderStream.build_nodes(builder)
        return BuilderStream(head=head, curr=head)


def piecewise(cons, start, stop, duration):
    pass


class PulseCompiler:
    def __init__(self, ast: Builder) -> None:
        self.stream = BuilderStream.create(ast)

    def read_address(self):
        spatial = self.stream.eat([Location, Uniform, Var], [Scale])
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
        wf_head = self.stream.eat(
            types=[Linear, Constant, Poly, PiecewiseConstant, PiecewiseLinear, Fn],
            skips=[Slice, Record],
        )
        curr = wf_head
        waveform: ir.Waveform = wf_head.node.__bloqade_ir__()
        while curr.next is not None:
            if isinstance(curr.node, Slice):
                waveform[slice(curr.node._start, curr.node._stop)]
            elif isinstance(curr.node, Record):
                waveform = waveform.record(curr.node._name)
            else:
                waveform = waveform.append(curr.node.__bloqade_ir__())
            curr = curr.next
            if not isinstance(curr.node, WaveformPrimitive):
                break
        return waveform

    def compile(self) -> ir.Sequence:
        pass
