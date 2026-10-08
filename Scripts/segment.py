"""Directed, weighted connection between two nodes."""

from __future__ import annotations

import math
from typing import Optional

from node import Node, ensure_node


class Segment:
    """A directed connection from an origin node to a destination node.

    Creating a segment also registers the destination as a neighbor of the
    origin. Path-finding and node plotting follow those neighbor links, so the
    two structures must never get out of sync; doing it here guarantees that.

    Attributes:
        origin: Node where the segment starts.
        destination: Node where the segment ends.
        cost: Weight of the segment (a distance in whatever unit the caller
            uses; kilometres for airspace data).
    """

    def __init__(
        self, origin: Node, destination: Node, cost: Optional[float] = None
    ) -> None:
        """Create a segment and link its endpoints.

        Args:
            origin: Node where the segment starts.
            destination: Node where the segment ends.
            cost: Weight of the segment. When omitted it defaults to the
                Euclidean distance between the endpoints, which suits the
                simple graph. For geographic nodes pass the cost explicitly
                (for example in km), because the default would be in degrees.

        Raises:
            TypeError: If either endpoint is not a Node (for example ``None``
                because a node name was not found).
            ValueError: If ``cost`` is not a finite, non-negative number.
        """
        self.origin: Node = ensure_node(origin, "Segment origin")
        self.destination: Node = ensure_node(destination, "Segment destination")
        self.cost: float = self._resolve_cost(cost)

        # Done last on purpose: if validation above fails, the origin node
        # must not be left with a neighbor that has no matching segment.
        self.origin.add_neighbor(self.destination)

    def _resolve_cost(self, cost: Optional[float]) -> float:
        """Return a validated cost, computing the default when none is given."""
        if cost is None:
            return self.origin.distance_to(self.destination)

        try:
            numeric_cost = float(cost)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Segment cost must be numeric, got {cost!r}.") from error

        # A negative or non-finite cost has no meaning as a distance and would
        # break shortest-path algorithms, so reject it at the source.
        if not math.isfinite(numeric_cost) or numeric_cost < 0:
            raise ValueError(
                f"Segment cost must be a finite, non-negative number, got {cost!r}."
            )
        return numeric_cost

    def __repr__(self) -> str:
        return (
            f"Segment(origin={self.origin.name!r}, "
            f"destination={self.destination.name!r}, cost={self.cost})"
        )
