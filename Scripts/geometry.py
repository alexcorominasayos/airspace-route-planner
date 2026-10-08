"""Pure geometry helpers shared across the project.

This module intentionally imports nothing from the rest of the project, so any
other module can use it without risking circular imports.
"""

from __future__ import annotations

import math

# Mean Earth radius in kilometres. The original code used 6,370,000 metres;
# keeping the same value makes the new distances match the old results.
EARTH_RADIUS_KM = 6370.0

MAX_LATITUDE_DEGREES = 90.0
MAX_LONGITUDE_DEGREES = 180.0


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Return the straight-line distance between two points on a flat plane.

    For nodes of the simple graph this is the natural segment length. For
    geographic coordinates the result is expressed in *degrees*, so it is only
    a cheap relative measure (for example an A* heuristic), never a real-world
    distance. Use :func:`haversine_distance_km` when kilometres are needed.

    Args:
        x1: Horizontal coordinate of the first point.
        y1: Vertical coordinate of the first point.
        x2: Horizontal coordinate of the second point.
        y2: Vertical coordinate of the second point.

    Returns:
        The distance, in the same unit as the inputs.
    """
    return math.hypot(x2 - x1, y2 - y1)


def validate_geographic_coordinates(latitude: float, longitude: float) -> None:
    """Check that a latitude/longitude pair is a valid position on Earth.

    Failing early here catches swapped or corrupted columns in data files
    before they turn into silently wrong distances or misplaced map points.

    Args:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.

    Raises:
        ValueError: If latitude is outside [-90, 90] or longitude is outside
            [-180, 180]. NaN values are rejected as well.
    """
    # Written as "not (a <= x <= b)" so that NaN, for which every comparison
    # is False, is rejected instead of slipping through.
    if not (-MAX_LATITUDE_DEGREES <= latitude <= MAX_LATITUDE_DEGREES):
        raise ValueError(
            f"Latitude must be between -{MAX_LATITUDE_DEGREES:g} and "
            f"{MAX_LATITUDE_DEGREES:g} degrees, got {latitude}."
        )
    if not (-MAX_LONGITUDE_DEGREES <= longitude <= MAX_LONGITUDE_DEGREES):
        raise ValueError(
            f"Longitude must be between -{MAX_LONGITUDE_DEGREES:g} and "
            f"{MAX_LONGITUDE_DEGREES:g} degrees, got {longitude}."
        )


def haversine_distance_km(
    latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float
) -> float:
    """Return the great-circle distance between two positions, in kilometres.

    Uses the haversine formula, which stays numerically accurate for the short
    distances typical between neighbouring navigation points.

    Args:
        latitude_a: Latitude of the first position, in degrees.
        longitude_a: Longitude of the first position, in degrees.
        latitude_b: Latitude of the second position, in degrees.
        longitude_b: Longitude of the second position, in degrees.

    Returns:
        The distance over the Earth's surface in kilometres.

    Raises:
        ValueError: If any coordinate is outside the valid geographic range.
    """
    validate_geographic_coordinates(latitude_a, longitude_a)
    validate_geographic_coordinates(latitude_b, longitude_b)

    lat_a = math.radians(latitude_a)
    lat_b = math.radians(latitude_b)
    delta_lat = lat_b - lat_a
    delta_lon = math.radians(longitude_b - longitude_a)

    # "Haversine" of the central angle between the two positions.
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )

    # Floating-point error can push the value marginally above 1 for nearly
    # antipodal points, which would make asin() raise; clamp it.
    central_angle = 2 * math.asin(min(1.0, math.sqrt(haversine)))
    return EARTH_RADIUS_KM * central_angle
