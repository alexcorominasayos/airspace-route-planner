"""Navigation point of the airspace (waypoint, fix or airport)."""

from __future__ import annotations

from geometry import haversine_distance_km, validate_geographic_coordinates
from node import Node


class NavPoint(Node):
    """A geographic point identified by a unique id and a human-readable name.

    It extends :class:`Node` instead of redefining name, coordinates and
    neighbors, so a ``Graph`` can hold navigation points directly and the
    path-finding code treats them like any other node.

    Coordinate convention (the same one the plotting and distance code relies
    on): ``x_coord`` is the longitude and ``y_coord`` is the latitude. That
    matches the (longitude, latitude) order expected by Basemap.

    Attributes:
        point_id: Unique identifier of the point in the airspace data files.
    """

    def __init__(
        self, point_id: str, name: str, longitude: float, latitude: float
    ) -> None:
        """Create a navigation point.

        Args:
            point_id: Unique identifier from the data file. Must not be blank.
            name: Public name of the point (for example an airport code).
            longitude: Longitude in decimal degrees, within [-180, 180].
            latitude: Latitude in decimal degrees, within [-90, 90].

        Raises:
            ValueError: If the id or name is blank, or the coordinates are
                not valid geographic values.
        """
        super().__init__(name, longitude, latitude)

        clean_id = str(point_id).strip()
        if not clean_id:
            raise ValueError(f"Navigation point '{self.name}' needs a non-empty id.")
        self.point_id: str = clean_id

        try:
            validate_geographic_coordinates(self.latitude, self.longitude)
        except ValueError as error:
            # Add which point is at fault; a bare "latitude out of range"
            # would be hard to trace back to a line of a large data file.
            raise ValueError(
                f"Invalid coordinates for navigation point '{self.name}' "
                f"(id {self.point_id}): {error}"
            ) from error

    @property
    def longitude(self) -> float:
        """Longitude in degrees (read-only alias of ``x_coord``)."""
        return self.x_coord

    @property
    def latitude(self) -> float:
        """Latitude in degrees (read-only alias of ``y_coord``)."""
        return self.y_coord

    def great_circle_distance_km_to(self, other: NavPoint) -> float:
        """Return the real-world distance to another navigation point in km.

        Unlike :meth:`Node.distance_to` (degrees), this follows the Earth's
        curvature and is the right measure for reporting route lengths.

        Raises:
            TypeError: If ``other`` is not a NavPoint.
        """
        if not isinstance(other, NavPoint):
            raise TypeError(
                f"great_circle_distance_km_to() needs a NavPoint, got {type(other).__name__}."
            )
        return haversine_distance_km(
            self.latitude, self.longitude, other.latitude, other.longitude
        )

    def __repr__(self) -> str:
        return (
            f"NavPoint(point_id={self.point_id!r}, name={self.name!r}, "
            f"longitude={self.longitude}, latitude={self.latitude})"
        )
