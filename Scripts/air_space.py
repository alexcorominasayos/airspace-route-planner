"""Airspace model: navigation points, the segments joining them and airports.

This module only describes and manipulates the data. Reading it from files is
done by ``data_loader`` and drawing it by the plotting module.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from graph import Graph
from nav_airport import NavAirport
from nav_point import NavPoint
from segment import Segment


class AirSpace:
    """A region of airspace made of navigation points, segments and airports.

    The three collections are exposed as read-only tuples and can only change
    through the ``add_*`` methods. That keeps the internal id index consistent
    with the point list, which a public mutable list could not guarantee.

    Methods that cannot do their job because something they refer to does not
    exist (an unknown id or airport name) return ``False``. The magic return
    codes of the original functions (``-1``, ``0`` and an implicit ``None``)
    are gone.
    """

    def __init__(self) -> None:
        self._nav_points: List[NavPoint] = []
        self._nav_segments: List[Segment] = []
        self._airports: List[NavAirport] = []

        # Segment files refer to points by id. Without this index every
        # segment would need a scan over all points, which is far too slow
        # for large data sets such as the whole European (ECAC) airspace.
        self._points_by_id: Dict[str, NavPoint] = {}

    @property
    def nav_points(self) -> Tuple[NavPoint, ...]:
        """All navigation points, airports included (read-only snapshot)."""
        return tuple(self._nav_points)

    @property
    def nav_segments(self) -> Tuple[Segment, ...]:
        """All segments between navigation points (read-only snapshot)."""
        return tuple(self._nav_segments)

    @property
    def airports(self) -> Tuple[NavAirport, ...]:
        """All airports (read-only snapshot)."""
        return tuple(self._airports)

    @property
    def is_empty(self) -> bool:
        """True when no navigation point has been loaded."""
        return not self._nav_points

    def add_point(self, nav_point: NavPoint) -> bool:
        """Add a navigation point and index it by its id.

        If another point already uses the same id, both are kept but the new
        one takes over the id lookup, mirroring the original loader where the
        last point with a repeated id won when segments were resolved.

        Args:
            nav_point: The point to add.

        Returns:
            True if added, False if this exact object was already present.

        Raises:
            TypeError: If ``nav_point`` is not a NavPoint.
        """
        if not isinstance(nav_point, NavPoint):
            raise TypeError(
                f"AirSpace points must be NavPoint objects, got {type(nav_point).__name__}."
            )
        if self._points_by_id.get(nav_point.point_id) is nav_point:
            return False

        self._nav_points.append(nav_point)
        self._points_by_id[nav_point.point_id] = nav_point
        return True

    def find_point_by_id(self, point_id: str) -> Optional[NavPoint]:
        """Return the point with the given id, or ``None`` if there is none."""
        return self._points_by_id.get(str(point_id).strip())

    def add_segment(
        self, origin_id: str, destination_id: str, cost: float
    ) -> bool:
        """Connect two existing points, looked up by id, with a new segment.

        Args:
            origin_id: Id of the point where the segment starts.
            destination_id: Id of the point where the segment ends.
            cost: Length of the segment in kilometres. It is required because
                the automatic default of :class:`Segment` is measured in
                degrees, which is meaningless for geographic data.

        Returns:
            True if the segment was created, False if either id is unknown.

        Raises:
            ValueError: If ``cost`` is missing or not a finite, non-negative
                number.
        """
        if cost is None:
            raise ValueError("Airspace segments need an explicit cost in kilometres.")

        origin = self.find_point_by_id(origin_id)
        destination = self.find_point_by_id(destination_id)
        if origin is None or destination is None:
            return False

        self._nav_segments.append(Segment(origin, destination, cost))
        return True

    def add_airport(self, airport: NavAirport) -> bool:
        """Register an airport, adding it to the navigation points if needed.

        Every airport is also a navigation point, so it can be used as a route
        endpoint; this method keeps both lists consistent.

        Args:
            airport: The airport to register.

        Returns:
            True if added, False if it was already registered.

        Raises:
            TypeError: If ``airport`` is not a NavAirport.
        """
        if not isinstance(airport, NavAirport):
            raise TypeError(
                f"AirSpace airports must be NavAirport objects, got {type(airport).__name__}."
            )
        if airport in self._airports:
            return False

        self.add_point(airport)
        self._airports.append(airport)
        return True

    def find_airport(self, name: str) -> Optional[NavAirport]:
        """Return the first airport called ``name``, or ``None`` if there is none."""
        return next((airport for airport in self._airports if airport.name == name), None)

    def add_sid(self, airport_name: str, sid_name: str) -> bool:
        """Register a departure procedure (SID) for an airport.

        Returns:
            True if the airport exists (the SID is added unless already
            listed), False if the airport is not in this airspace.

        Raises:
            ValueError: If ``sid_name`` is blank.
        """
        return self._register_procedure(airport_name, NavAirport.add_sid, sid_name)

    def add_star(self, airport_name: str, star_name: str) -> bool:
        """Register an arrival procedure (STAR) for an airport.

        Returns:
            True if the airport exists (the STAR is added unless already
            listed), False if the airport is not in this airspace.

        Raises:
            ValueError: If ``star_name`` is blank.
        """
        return self._register_procedure(airport_name, NavAirport.add_star, star_name)

    def _register_procedure(
        self,
        airport_name: str,
        add_procedure: Callable[[NavAirport, str], bool],
        procedure_name: str,
    ) -> bool:
        """Find an airport by name and register a procedure on it.

        The airport search was duplicated in the original ``addSID`` and
        ``addSTAR``; sharing it keeps one implementation to maintain.
        """
        airport = self.find_airport(airport_name)
        if airport is None:
            return False
        add_procedure(airport, procedure_name)
        return True

    def build_graph(self) -> Graph:
        """Return a graph with this airspace's points and segments.

        The graph gets its own lists but shares the node and segment objects
        with the airspace. Neighbor links live on the nodes themselves, so the
        graph is immediately ready for path-finding.
        """
        return Graph(nodes=self._nav_points, segments=self._nav_segments)

    def __repr__(self) -> str:
        return (
            f"AirSpace(points={len(self._nav_points)}, "
            f"segments={len(self._nav_segments)}, airports={len(self._airports)})"
        )
