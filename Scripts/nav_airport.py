"""Airport of the airspace, together with its departure and arrival procedures."""

from __future__ import annotations

from typing import List, Tuple

from nav_point import NavPoint


class NavAirport(NavPoint):
    """A navigation point that is also an airport.

    The original ``navAirport`` only stored a name, while the loader filled the
    airport list with plain navigation points, so the list held two unrelated
    kinds of object. Extending :class:`NavPoint` fixes that: an airport has real
    coordinates, is a full graph node, and can be plotted, exported to KML and
    used as a route endpoint like any other point.

    Two kinds of published flight procedure are tracked per airport:

    * SID  - Standard Instrument Departure, how aircraft leave the airport.
    * STAR - Standard Terminal Arrival Route, how aircraft arrive at it.
    """

    def __init__(
        self, point_id: str, name: str, longitude: float, latitude: float
    ) -> None:
        """Create an airport without any procedures yet.

        Args:
            point_id: Unique identifier from the data file.
            name: Airport name (for example its ICAO code).
            longitude: Longitude in decimal degrees.
            latitude: Latitude in decimal degrees.

        Raises:
            ValueError: If the id or name is blank, or the coordinates are
                not valid geographic values.
        """
        super().__init__(point_id, name, longitude, latitude)
        self._sids: List[str] = []
        self._stars: List[str] = []

    @property
    def sids(self) -> Tuple[str, ...]:
        """Names of the departure procedures (read-only snapshot)."""
        return tuple(self._sids)

    @property
    def stars(self) -> Tuple[str, ...]:
        """Names of the arrival procedures (read-only snapshot)."""
        return tuple(self._stars)

    def add_sid(self, sid_name: str) -> bool:
        """Register a departure procedure.

        Returns:
            True if it was added, False if it was already registered.

        Raises:
            ValueError: If ``sid_name`` is blank.
        """
        return self._add_unique_procedure(self._sids, sid_name, "SID")

    def add_star(self, star_name: str) -> bool:
        """Register an arrival procedure.

        Returns:
            True if it was added, False if it was already registered.

        Raises:
            ValueError: If ``star_name`` is blank.
        """
        return self._add_unique_procedure(self._stars, star_name, "STAR")

    @staticmethod
    def _add_unique_procedure(
        procedures: List[str], procedure_name: str, kind: str
    ) -> bool:
        """Append a procedure name unless blank or already listed.

        SIDs and STARs follow exactly the same rules, so the logic lives in
        one place instead of being copied into two near-identical methods.
        """
        clean_name = str(procedure_name).strip()
        if not clean_name:
            raise ValueError(f"A {kind} needs a non-empty name.")
        if clean_name in procedures:
            return False
        procedures.append(clean_name)
        return True

    def __repr__(self) -> str:
        return (
            f"NavAirport(point_id={self.point_id!r}, name={self.name!r}, "
            f"longitude={self.longitude}, latitude={self.latitude}, "
            f"sids={len(self._sids)}, stars={len(self._stars)})"
        )
