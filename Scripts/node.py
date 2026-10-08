"""Basic graph vertex.

``Node`` is used directly by the simple (flat plane) graph and, through
inheritance, by the airspace navigation points, so both kinds of vertex share
a single implementation of names, coordinates and neighbor handling.
"""

from __future__ import annotations

import math
from typing import List

from geometry import euclidean_distance


class Node:
    """A named point on a 2D plane that knows which nodes it connects to.

    The neighbor list lives on the node (and not only in the graph's segment
    list) so path-finding can walk from node to node directly instead of
    searching every segment each time.

    Attributes:
        name: Label used to display and look up the node.
        x_coord: Horizontal coordinate.
        y_coord: Vertical coordinate.
        neighbors: Nodes that can be reached directly from this one.
    """

    def __init__(self, name: str, x_coord: float, y_coord: float) -> None:
        """Create a node.

        Values read from text files arrive as strings, so numeric strings are
        accepted for the coordinates and converted to floats.

        Args:
            name: Label of the node. Must not be blank.
            x_coord: Horizontal coordinate.
            y_coord: Vertical coordinate.

        Raises:
            ValueError: If the name is blank or a coordinate is not a finite
                number.
        """
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("A node needs a non-empty name.")

        self.name: str = clean_name
        self.x_coord: float = self._parse_coordinate(x_coord, "x", clean_name)
        self.y_coord: float = self._parse_coordinate(y_coord, "y", clean_name)
        self.neighbors: List[Node] = []

    @staticmethod
    def _parse_coordinate(value: object, axis: str, node_name: str) -> float:
        """Convert ``value`` to a finite float or raise a descriptive error."""
        try:
            coordinate = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Node '{node_name}' has a non-numeric {axis} coordinate: {value!r}."
            ) from error

        # NaN and infinity parse fine as floats but would corrupt every
        # distance calculation and plot that uses this node.
        if not math.isfinite(coordinate):
            raise ValueError(
                f"Node '{node_name}' has a non-finite {axis} coordinate: {value!r}."
            )
        return coordinate

    def add_neighbor(self, other: Node) -> bool:
        """Register ``other`` as directly reachable from this node.

        Args:
            other: The node to connect to.

        Returns:
            True if the neighbor was added, False if it was already present.

        Raises:
            TypeError: If ``other`` is not a Node.
        """
        ensure_node(other, "Neighbor")
        if other in self.neighbors:
            return False
        self.neighbors.append(other)
        return True

    def distance_to(self, other: Node) -> float:
        """Return the straight-line (Euclidean) distance to another node.

        For geographic nodes this is measured in degrees, not kilometres; see
        :func:`geometry.euclidean_distance`.

        Raises:
            TypeError: If ``other`` is not a Node.
        """
        ensure_node(other, "distance_to() argument")
        return euclidean_distance(
            self.x_coord, self.y_coord, other.x_coord, other.y_coord
        )

    def __repr__(self) -> str:
        # Neighbors are deliberately left out: they reference other nodes
        # (possibly this one) and would make the output huge or recursive.
        return (
            f"{type(self).__name__}(name={self.name!r}, "
            f"x_coord={self.x_coord}, y_coord={self.y_coord})"
        )


def ensure_node(value: object, label: str) -> Node:
    """Return ``value`` if it is a Node, otherwise raise a clear TypeError.

    Shared by ``Node``, ``Segment`` and ``Graph`` so every type check produces
    the same style of error message.

    Args:
        value: The object to check.
        label: Human-readable role of the object, used in the error message.

    Raises:
        TypeError: If ``value`` is not a Node (for example ``None`` when a
            node name could not be resolved).
    """
    if not isinstance(value, Node):
        raise TypeError(f"{label} must be a Node, got {type(value).__name__}.")
    return value
