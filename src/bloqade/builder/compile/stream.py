from dataclasses import dataclass
from typing import Optional, List, Type
from ..base import Builder


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
