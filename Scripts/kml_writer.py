"""Export of navigation points and routes to KML files for Google Earth.

KML is XML, so text is escaped before being written (an ampersand in a name
used to produce a file Google Earth could not open) and every document is
built completely in memory before any file is touched, so a failure can never
leave a half-written file behind.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Iterable, List
from xml.sax.saxutils import escape

from nav_point import NavPoint

KML_EXTENSION = ".kml"
KML_NAMESPACE = "http://www.opengis.net/kml/2.2"
GX_NAMESPACE = "http://www.google.com/kml/ext/2.2"

# The animated track needs timestamps, but a route has no real schedule. Each
# stop is simply placed one hour after the previous one, from an arbitrary date.
ANIMATION_START = datetime(2024, 1, 1)
ANIMATION_STEP = timedelta(hours=1)
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

MIN_ROUTE_POINTS = 2  # A line needs at least a start and an end.


def write_points_kml(points: Iterable[NavPoint], file_path: str) -> str:
    """Write navigation points to a KML file as one placemark each.

    Args:
        points: The navigation points to export (airports, waypoints...).
        file_path: Destination file. ``.kml`` is appended if missing.

    Returns:
        The path of the file that was written.

    Raises:
        ValueError: If there are no points or the file name is blank.
        TypeError: If an item is not a NavPoint (plain nodes of the simple
            graph have no geographic coordinates).
        OSError: If the file cannot be written.
    """
    nav_points = _require_nav_points(points)
    if not nav_points:
        raise ValueError("There are no points to export.")

    placemarks = [_point_placemark(point) for point in nav_points]
    return _write_document(file_path, placemarks)


def write_route_kml(route: Iterable[NavPoint], file_path: str) -> str:
    """Write a route to a KML file.

    The document contains the route as a line on the ground, one placemark per
    stop, and an animated track that Google Earth can play back.

    Args:
        route: Navigation points in travel order (a ``Route`` works).
        file_path: Destination file. ``.kml`` is appended if missing.

    Returns:
        The path of the file that was written.

    Raises:
        ValueError: If the route has fewer than two points or the file name
            is blank.
        TypeError: If a stop is not a NavPoint.
        OSError: If the file cannot be written.
    """
    stops = _require_nav_points(route)
    if len(stops) < MIN_ROUTE_POINTS:
        raise ValueError(
            f"A route needs at least {MIN_ROUTE_POINTS} points to be exported, got {len(stops)}."
        )

    placemarks = [_route_line_placemark(stops)]
    placemarks.extend(_point_placemark(stop) for stop in stops)
    placemarks.append(_animated_track_placemark(stops))
    return _write_document(file_path, placemarks)


# --------------------------------------------------------------------------
# Document building
# --------------------------------------------------------------------------

def _point_placemark(point: NavPoint) -> str:
    """Return the placemark of a single point (shared by both exports)."""
    return (
        "    <Placemark>\n"
        f"        <name>{escape(point.name)}</name>\n"
        "        <Point>\n"
        f"            <coordinates>{_coordinates(point)}</coordinates>\n"
        "        </Point>\n"
        "    </Placemark>\n"
    )


def _route_line_placemark(stops: List[NavPoint]) -> str:
    """Return the placemark drawing the whole route as one line on the ground."""
    route_name = ", ".join(stop.name for stop in stops)
    coordinate_lines = "\n".join(f"                {_coordinates(stop)}" for stop in stops)
    return (
        "    <Placemark>\n"
        f"        <name>Route: {escape(route_name)}</name>\n"
        "        <LineString>\n"
        "            <altitudeMode>clampToGround</altitudeMode>\n"
        "            <extrude>1</extrude>\n"
        "            <tessellate>1</tessellate>\n"
        "            <coordinates>\n"
        f"{coordinate_lines}\n"
        "            </coordinates>\n"
        "        </LineString>\n"
        "    </Placemark>\n"
    )


def _animated_track_placemark(stops: List[NavPoint]) -> str:
    """Return a gx:Track placemark that Google Earth can animate over time."""
    entries = []
    for index, stop in enumerate(stops):
        # datetime arithmetic rolls over into the next day by itself. The old
        # code formatted the stop number as the hour, which produced invalid
        # times such as "T24:00:00Z" for routes with more than 24 stops.
        timestamp = (ANIMATION_START + index * ANIMATION_STEP).strftime(TIMESTAMP_FORMAT)
        entries.append(
            f"            <when>{timestamp}</when>\n"
            f"            <gx:coord>{stop.longitude} {stop.latitude} 0</gx:coord>\n"
        )
    return (
        "    <Placemark>\n"
        "        <name>Animated Path</name>\n"
        "        <gx:Track>\n"
        f"{''.join(entries)}"
        "        </gx:Track>\n"
        "    </Placemark>\n"
    )


def _coordinates(point: NavPoint) -> str:
    """Format a point the way KML expects: ``longitude,latitude``."""
    return f"{point.longitude},{point.latitude}"


def _write_document(file_path: str, placemarks: List[str]) -> str:
    """Wrap placemarks in a KML document and write it to disk in one go."""
    destination = _with_kml_extension(file_path)
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<kml xmlns="{KML_NAMESPACE}" xmlns:gx="{GX_NAMESPACE}">\n'
        "<Document>\n"
        f"{''.join(placemarks)}"
        "</Document>\n"
        "</kml>\n"
    )
    with open(destination, "w", encoding="utf-8") as kml_file:
        kml_file.write(document)
    return destination


def _with_kml_extension(file_path: str) -> str:
    """Return the file name with a ``.kml`` extension, adding it if absent."""
    clean_path = os.fspath(file_path).strip()
    if not clean_path:
        raise ValueError("The KML file name must not be empty.")
    if not clean_path.lower().endswith(KML_EXTENSION):
        clean_path += KML_EXTENSION
    return clean_path


def _require_nav_points(items: Iterable[NavPoint]) -> List[NavPoint]:
    """Return the items as a list, making sure each one has geographic coordinates."""
    nav_points = list(items)
    for item in nav_points:
        if not isinstance(item, NavPoint):
            raise TypeError(
                "KML export needs navigation points with geographic coordinates, "
                f"got {type(item).__name__}."
            )
    return nav_points
