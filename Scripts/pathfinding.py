"""Routes through a graph and the A* search that finds the shortest one.

Distance math lives in ``geometry`` and drawing in the plotting module; this
module only knows about routes and how to find them.
"""

from __future__ import annotations

import heapq
import itertools
import math
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from graph import Graph
from nav_point import NavPoint
from node import Node, ensure_node

# A function that measures the distance between two nodes. Used both as the
# cost of moving along an edge and as the A* "distance to goal" estimate.
DistanceFunction = Callable[[Node, Node], float]


class Route:
    """An ordered chain of nodes where each node is a neighbor of the previous one.

    This replaces the old ``path`` class, whose name clashed with the many local
    variables called ``path`` and whose ``totalCost`` attribute only existed
    when a distance list happened to be passed in.
    """

    def __init__(self, nodes: Optional[Iterable[Node]] = None) -> None:
        """Create a route, optionally from an initial sequence of nodes.

        Args:
            nodes: Nodes in travel order. Each one must be a neighbor of the
                node before it.

        Raises:
            TypeError: If an item is not a Node.
            ValueError: If two consecutive nodes are not connected.
        """
        self._nodes: List[Node] = []
        for node in nodes or []:
            if not self.add_node(node):
                raise ValueError(
                    f"Node '{node.name}' is not a neighbor of "
                    f"'{self._nodes[-1].name}', so it cannot continue the route."
                )

    # -- Sequence-like access ------------------------------------------------

    @property
    def nodes(self) -> Tuple[Node, ...]:
        """The nodes of the route in travel order (read-only snapshot)."""
        return tuple(self._nodes)

    @property
    def names(self) -> List[str]:
        """The node names in travel order, handy for printing."""
        return [node.name for node in self._nodes]

    @property
    def origin(self) -> Optional[Node]:
        """First node of the route, or ``None`` if the route is empty."""
        return self._nodes[0] if self._nodes else None

    @property
    def destination(self) -> Optional[Node]:
        """Last node of the route, or ``None`` if the route is empty."""
        return self._nodes[-1] if self._nodes else None

    def __len__(self) -> int:
        return len(self._nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self._nodes)

    def __getitem__(self, index: int) -> Node:
        return self._nodes[index]

    # -- Building and querying -----------------------------------------------

    def add_node(self, node: Node) -> bool:
        """Append a node if it can legally continue the route.

        The first node is always accepted. Any later node must be a neighbor of
        the current last node. (The original ``addNodeToPath`` checked the node
        that happened to precede it in the *graph's* node list instead, which
        was a bug.)

        Returns:
            True if the node was appended, False if it is not connected to the
            end of the route.

        Raises:
            TypeError: If ``node`` is not a Node.
        """
        ensure_node(node, "Route node")
        if self._nodes and node not in self._nodes[-1].neighbors:
            return False
        self._nodes.append(node)
        return True

    def contains_node(self, name: str) -> bool:
        """Return True if some node of the route is called ``name``."""
        return any(node.name == name for node in self._nodes)

    def straight_line_distance_from_origin(self, name: str) -> Optional[float]:
        """Return the straight-line distance from the origin to a node of the route.

        Previously ``getCostToNode``. The name now states what it computes: a
        direct (Euclidean) distance, *not* the length travelled along the route.

        Returns:
            The distance, or ``None`` if the route is empty or has no node
            called ``name`` (replacing the old ``-1`` marker).
        """
        origin = self.origin
        if origin is None:
            return None
        target = next((node for node in self._nodes if node.name == name), None)
        if target is None:
            return None
        return origin.distance_to(target)

    def estimate_remaining_distance(
        self, graph: Graph, destination_name: str
    ) -> Optional[float]:
        """Return the straight-line distance from the end of the route to a graph node.

        This is the "how far is the goal" estimate used by A* (previously
        ``getApproxToDest``).

        Returns:
            The distance, or ``None`` if the route is empty or the graph has
            no node called ``destination_name`` (replacing the old ``-1``).
        """
        last_node = self.destination
        target = graph.find_node(destination_name)
        if last_node is None or target is None:
            return None
        return last_node.distance_to(target)

    # -- Measuring -----------------------------------------------------------

    def euclidean_length(self) -> float:
        """Return the summed straight-line length of every leg.

        Suited to the simple graph. For geographic routes the unit is degrees;
        use :meth:`great_circle_length_km` there.
        """
        return sum(start.distance_to(end) for start, end in self._legs())

    def great_circle_length_km(self) -> float:
        """Return the real-world length of the route in kilometres.

        Previously ``totalCost``. The value is not rounded; round it when
        displaying it so no precision is lost for further calculations.

        Raises:
            TypeError: If any node is not a NavPoint, since only navigation
                points have geographic coordinates.
        """
        if not all(isinstance(node, NavPoint) for node in self._nodes):
            raise TypeError(
                "great_circle_length_km() needs every node to be a NavPoint."
            )
        return sum(start.great_circle_distance_km_to(end) for start, end in self._legs())

    def _legs(self) -> Iterator[Tuple[Node, Node]]:
        """Yield each pair of consecutive nodes of the route."""
        return zip(self._nodes, self._nodes[1:])

    def __repr__(self) -> str:
        return f"Route({self.names})"


def find_shortest_path(
    graph: Graph,
    start_name: str,
    goal_name: str,
    distance: DistanceFunction = Node.distance_to,
) -> Optional[Route]:
    """Find the shortest route between two nodes with the A* algorithm.

    Routes follow each node's neighbor links; the graph is only used to turn
    the two names into nodes.

    By default distances are Euclidean, exactly as in the original code. For
    geographic graphs that means the route is the shortest one *in degrees of
    longitude/latitude*, which is only an approximation of the shortest one in
    kilometres. To optimise real distances pass
    ``distance=NavPoint.great_circle_distance_km_to``. The same function is used
    for the edge cost and for the estimate to the goal, which keeps A* optimal.

    Compared to the original implementation this one keeps node scores in
    dictionaries and the frontier in a priority queue. The original called
    ``list.index`` and ``min`` over lists inside the main loop, which made the
    search get dramatically slower as the airspace grew.

    Args:
        graph: Graph used to look the start and goal up by name.
        start_name: Name of the first node of the route.
        goal_name: Name of the last node of the route.
        distance: Function measuring the distance between two nodes.

    Returns:
        The shortest Route, or ``None`` if the goal cannot be reached.

    Raises:
        ValueError: If either name does not exist in the graph.
    """
    start = _require_node(graph, start_name, "Start")
    goal = _require_node(graph, goal_name, "Destination")

    # Cheapest known cost to reach each discovered node, and the node we came
    # from on that cheapest route (used to rebuild the route at the end).
    cost_so_far: Dict[Node, float] = {start: 0.0}
    came_from: Dict[Node, Node] = {}

    # Heap entries are (estimated total cost, insertion number, cost so far,
    # node). The insertion number breaks ties first-in-first-out and, because
    # it is unique, stops Python from ever trying to compare two nodes.
    insertion_counter = itertools.count()
    frontier: List[Tuple[float, int, float, Node]] = [
        (distance(start, goal), next(insertion_counter), 0.0, start)
    ]

    while frontier:
        _, _, cost_to_current, current = heapq.heappop(frontier)

        if current is goal:
            return Route(_rebuild_path(came_from, goal))

        # A node is queued again whenever a cheaper way to it is found, so the
        # heap can still hold older, more expensive entries for it. Skip them.
        if cost_to_current > cost_so_far[current]:
            continue

        for neighbor in current.neighbors:
            cost_via_current = cost_to_current + distance(current, neighbor)
            if cost_via_current < cost_so_far.get(neighbor, math.inf):
                cost_so_far[neighbor] = cost_via_current
                came_from[neighbor] = current
                estimated_total = cost_via_current + distance(neighbor, goal)
                heapq.heappush(
                    frontier,
                    (estimated_total, next(insertion_counter), cost_via_current, neighbor),
                )

    return None


def _require_node(graph: Graph, name: str, role: str) -> Node:
    """Return the node called ``name`` or raise a descriptive ValueError."""
    node = graph.find_node(name)
    if node is None:
        raise ValueError(f"{role} node '{name}' is not in the graph.")
    return node


def _rebuild_path(came_from: Dict[Node, Node], goal: Node) -> List[Node]:
    """Walk the ``came_from`` links backwards from the goal to the start."""
    path = [goal]
    while path[-1] in came_from:
        path.append(came_from[path[-1]])
    path.reverse()
    return path
