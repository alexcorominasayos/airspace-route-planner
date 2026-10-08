"""Directed graph container made of nodes and segments.

Only data storage and lookup live here. Drawing is handled by a separate
plotting module and reading graphs from files by a separate loader module, so
this class can be reused and tested without matplotlib or the file system.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from node import Node, ensure_node
from segment import Segment


class Graph:
    """A directed graph of :class:`Node` objects joined by :class:`Segment` objects.

    Attributes:
        nodes: All vertices of the graph.
        segments: All directed, weighted edges of the graph.
    """

    def __init__(
        self,
        nodes: Optional[Iterable[Node]] = None,
        segments: Optional[Iterable[Segment]] = None,
    ) -> None:
        """Create a graph, optionally pre-filled with nodes and segments.

        The incoming iterables are copied. ``None`` defaults (instead of
        ``[]``) avoid Python's shared-mutable-default pitfall, and copying
        stops the graph from silently aliasing the caller's lists.

        Args:
            nodes: Initial nodes. Defaults to an empty graph.
            segments: Initial segments. Their endpoints are expected to be
                among ``nodes``; this is not re-checked, to keep bulk loading
                of large airspaces fast.

        Raises:
            TypeError: If any item is not a Node / Segment respectively.
        """
        self.nodes: List[Node] = [
            ensure_node(node, "Every graph node") for node in (nodes or [])
        ]
        self.segments: List[Segment] = list(segments or [])
        for segment in self.segments:
            if not isinstance(segment, Segment):
                raise TypeError(
                    f"Every graph segment must be a Segment, got {type(segment).__name__}."
                )

    @property
    def is_empty(self) -> bool:
        """True when the graph has no nodes."""
        return not self.nodes

    def find_node(self, name: str) -> Optional[Node]:
        """Return the first node called ``name``, or ``None`` if there is none.

        Names are not enforced to be unique, so when several nodes share a
        name the first one wins.
        """
        return next((node for node in self.nodes if node.name == name), None)

    def has_node(self, name: str) -> bool:
        """Return True if a node called ``name`` exists in the graph."""
        return self.find_node(name) is not None

    def add_node(self, node: Node) -> bool:
        """Add a node unless that exact object is already in the graph.

        Uniqueness is by object identity, not by name: airspace data may
        legitimately contain different points that share a name, and dropping
        them would break the segments that refer to them.

        Args:
            node: The node to add.

        Returns:
            True if the node was added, False if it was already present.

        Raises:
            TypeError: If ``node`` is not a Node.
        """
        ensure_node(node, "Graph node")
        if node in self.nodes:
            return False
        self.nodes.append(node)
        return True

    def add_segment(
        self,
        origin_name: str,
        destination_name: str,
        cost: Optional[float] = None,
    ) -> bool:
        """Connect two existing nodes, looked up by name, with a new segment.

        Args:
            origin_name: Name of the node where the segment starts.
            destination_name: Name of the node where the segment ends.
            cost: Segment weight. Defaults to the Euclidean distance between
                the two nodes (see :class:`Segment`).

        Returns:
            True if the segment was created, False if either node name does
            not exist in the graph.

        Raises:
            ValueError: If ``cost`` is not a finite, non-negative number.
        """
        origin = self.find_node(origin_name)
        destination = self.find_node(destination_name)
        if origin is None or destination is None:
            return False

        self.segments.append(Segment(origin, destination, cost))
        return True

    def __repr__(self) -> str:
        return f"Graph(nodes={len(self.nodes)}, segments={len(self.segments)})"
