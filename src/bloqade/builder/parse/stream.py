"""
Module for managing a stream of builder nodes.

This module provides classes to represent builder nodes and builder streams. A builder node is a single
element in the stream, representing a step in a construction process. A builder stream is a sequence
of builder nodes, allowing traversal and manipulation of the construction steps.
"""

from dataclasses import dataclass
from typing import Optional, List, Type
from bloqade.builder.base import Builder


@dataclass
class BuilderNode:
    """A node in the builder stream."""

    node: Builder
    next: Optional["BuilderNode"] = None

    def __repr__(self) -> str:
        """Representation of the BuilderNode."""
        return repr(self.node)


@dataclass
class BuilderStream:
    """Represents a stream of builder nodes."""

    head: BuilderNode
    curr: Optional[BuilderNode] = None

    def copy(self) -> "BuilderStream":
        """Create a copy of the builder stream."""
        return BuilderStream(head=self.head, curr=self.curr)

    def read(self) -> Optional[BuilderNode]:
        """Read the next builder node from the stream."""
        if self.curr is None:
            return None

        node = self.curr
        self.curr = self.curr.next
        return node

    def read_next(self, builder_types: List[type[Builder]]) -> Optional[BuilderNode]:
        """
        Read the next builder node of specified types from the stream.

        Args:
            builder_types (List[type[Builder]]): List of builder types to read from the stream.

        Returns:
            Optional[BuilderNode]: The next builder node matching one of the specified types, or None if not found.
        """
        node = self.read()
        while node is not None:
            if type(node.node) in builder_types:
                return node
            node = self.read()
        return None

    def eat(
        self, types: List[Type[Builder]], skips: Optional[List[Type[Builder]]] = None
    ) -> BuilderNode:
        """
        Move the stream pointer until a node of specified types is found.

        Args:
            types (List[Type[Builder]]): List of types to move the stream pointer to.
            skips (List[Type[Builder]] | None, optional): List of types to end the stream scan.

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
        """Iterator method to iterate over the builder stream."""
        return self

    def __next__(self):
        """Next method to get the next item in the builder stream."""
        node = self.read()
        if node is None:
            raise StopIteration
        return node

    @staticmethod
    def build_nodes(node: Builder) -> "BuilderNode":
        """
        Build BuilderNode instances from the provided Builder.

        Args:
            node (Builder): The root Builder instance.

        Returns:
            BuilderNode: The head of the linked list of BuilderNodes.
        """
        curr = node
        node = None
        while curr is not None:
            next = curr
            curr = curr.__parent__ if hasattr(curr, "__parent__") else None
            node = BuilderNode(next, node)

        return node

    @staticmethod
    def create(builder: Builder) -> "BuilderStream":
        """
        Create a BuilderStream instance from a Builder.

        Args:
            builder (Builder): The root Builder instance.

        Returns:
            BuilderStream: The created BuilderStream instance.
        """
        head = BuilderStream.build_nodes(builder)
        return BuilderStream(head=head, curr=head)
