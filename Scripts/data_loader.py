"""Reading of the project's text data files into model objects.

All parsing lives here, so the model classes (``Graph``, ``AirSpace``) stay
free of file handling and the menu stays free of parsing details.

Expected file layouts (fields separated by any amount of whitespace; extra
trailing fields are ignored, blank lines are skipped):

* simple graph points:   ``<name> <x> <y>``
* simple graph segments: ``<origin name> <destination name> <cost>``
* airspace nav points:   ``<id> <name> <latitude> <longitude>``
* airspace segments:     ``<origin id> <destination id> <cost>``
* airspace airports:     ``<airport name>`` (one per line)

Problems are handled in two ways. A malformed line aborts the load with a
:class:`DataFileFormatError` naming the file and line, because guessing what
the data meant would hide mistakes. A well-formed segment that refers to an
unknown point is skipped and reported through ``logging``, so the rest of a
large file can still be used.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Dict, Iterator, List, NamedTuple, Sequence, Set, Union

from air_space import AirSpace
from graph import Graph
from nav_airport import NavAirport
from nav_point import NavPoint
from node import Node

logger = logging.getLogger(__name__)

PathLike = Union[str, "os.PathLike[str]"]

# "utf-8-sig" behaves like UTF-8 but also silently drops the invisible byte
# order mark some Windows editors add, which would otherwise corrupt the first
# id or name of a file. Change this one constant if your files use another
# encoding (for example "latin-1").
DATA_FILE_ENCODING = "utf-8-sig"

# Minimum number of fields each kind of line must contain.
MIN_SIMPLE_POINT_FIELDS = 3
MIN_SIMPLE_SEGMENT_FIELDS = 3
MIN_NAV_POINT_FIELDS = 4
MIN_NAV_SEGMENT_FIELDS = 3
MIN_AIRPORT_FIELDS = 1

# Warnings list at most this many examples, so a badly broken file does not
# flood the console.
MAX_REPORTED_PROBLEMS = 5


class DataFileFormatError(ValueError):
    """Raised when a data file contains a line that cannot be interpreted.

    It subclasses ``ValueError`` so callers that already handle invalid values
    keep working, while the message always names the file and line.
    """


class DataRecord(NamedTuple):
    """One non-blank line of a data file, split into fields."""

    line_number: int
    fields: List[str]


def load_simple_graph(points_path: PathLike, segments_path: PathLike) -> Graph:
    """Load a simple (flat plane) graph from a points file and a segments file.

    Args:
        points_path: File with one ``<name> <x> <y>`` node per line.
        segments_path: File with one ``<origin> <destination> <cost>`` segment
            per line. Segments naming an unknown node are skipped and logged.

    Returns:
        A new graph. Nothing is shared with previously loaded graphs, so
        loading twice can no longer append duplicates to the same graph.

    Raises:
        FileNotFoundError: If either file does not exist.
        DataFileFormatError: If a line is malformed.
    """
    graph = Graph()

    for record in _read_records(points_path, MIN_SIMPLE_POINT_FIELDS):
        name, x_coord, y_coord = record.fields[:3]
        with _line_context(points_path, record.line_number):
            graph.add_node(Node(name, x_coord, y_coord))

    skipped_segments: List[str] = []
    for record in _read_records(segments_path, MIN_SIMPLE_SEGMENT_FIELDS):
        origin_name, destination_name, cost = record.fields[:3]
        with _line_context(segments_path, record.line_number):
            was_created = graph.add_segment(origin_name, destination_name, cost)
        if not was_created:
            skipped_segments.append(
                f"{origin_name}->{destination_name} (line {record.line_number})"
            )

    _log_data_warning(
        segments_path, "segments skipped because a node does not exist", skipped_segments
    )
    return graph


def load_airspace(
    nav_points_path: PathLike, segments_path: PathLike, airports_path: PathLike
) -> AirSpace:
    """Load an airspace from its three data files.

    The airspace is built from scratch and only returned once every file has
    been read, so a failure can never leave a half-loaded airspace behind (the
    original loader filled the caller's object while reading).

    Args:
        nav_points_path: File with ``<id> <name> <latitude> <longitude>`` lines.
        segments_path: File with ``<origin id> <destination id> <cost>`` lines.
        airports_path: File listing airport names. Every navigation point whose
            name is listed becomes an airport; names without a matching point
            are ignored (and reported at INFO level).

    Returns:
        A new, fully loaded airspace.

    Raises:
        FileNotFoundError: If any file does not exist.
        DataFileFormatError: If a line is malformed.
    """
    airport_names = _read_airport_names(airports_path)
    air_space = AirSpace()

    airports_by_name = _load_nav_points(
        air_space, nav_points_path, set(airport_names)
    )
    _load_nav_segments(air_space, segments_path)
    _register_airports(air_space, airport_names, airports_by_name, airports_path)
    return air_space


def load_airspace_by_prefix(data_dir: PathLike, prefix: str) -> AirSpace:
    """Load the airspace stored in ``<prefix>_nav.txt``, ``_seg.txt`` and ``_aer.txt``.

    Keeps the project's file naming convention in one place instead of
    spreading it through the menu.

    Args:
        data_dir: Folder containing the data files.
        prefix: Common start of the three file names, e.g. ``"Cat"``.

    Raises:
        ValueError: If ``prefix`` is blank.
        FileNotFoundError: If any of the three files is missing.
        DataFileFormatError: If a line is malformed.
    """
    clean_prefix = prefix.strip()
    if not clean_prefix:
        raise ValueError("The airspace file prefix must not be empty.")

    return load_airspace(
        os.path.join(data_dir, f"{clean_prefix}_nav.txt"),
        os.path.join(data_dir, f"{clean_prefix}_seg.txt"),
        os.path.join(data_dir, f"{clean_prefix}_aer.txt"),
    )


# --------------------------------------------------------------------------
# Airspace loading steps
# --------------------------------------------------------------------------

def _read_airport_names(airports_path: PathLike) -> List[str]:
    """Return the airport names of the file, without repeats, in file order."""
    names = [
        record.fields[0]
        for record in _read_records(airports_path, MIN_AIRPORT_FIELDS)
    ]
    # dict.fromkeys removes repeated names while keeping the first-seen order,
    # which is the order airports are later listed to the user.
    return list(dict.fromkeys(names))


def _load_nav_points(
    air_space: AirSpace, nav_points_path: PathLike, airport_names: Set[str]
) -> Dict[str, List[NavAirport]]:
    """Fill ``air_space`` with points and return the airports found by name.

    Points whose name is listed as an airport are created directly as
    :class:`NavAirport`. That way the airport and the navigation point are the
    very same object and no second, disconnected copy is needed.
    """
    airports_by_name: Dict[str, List[NavAirport]] = {}
    repeated_ids: List[str] = []

    for record in _read_records(nav_points_path, MIN_NAV_POINT_FIELDS):
        point_id, name, latitude, longitude = record.fields[:4]

        with _line_context(nav_points_path, record.line_number):
            if name in airport_names:
                airport = NavAirport(
                    point_id, name, longitude=longitude, latitude=latitude
                )
                airports_by_name.setdefault(name, []).append(airport)
                nav_point: NavPoint = airport
            else:
                nav_point = NavPoint(
                    point_id, name, longitude=longitude, latitude=latitude
                )

        if air_space.find_point_by_id(nav_point.point_id) is not None:
            repeated_ids.append(f"{nav_point.point_id} (line {record.line_number})")
        air_space.add_point(nav_point)

    _log_data_warning(
        nav_points_path,
        "repeated ids found; all points are kept and the last one is used by segments",
        repeated_ids,
    )
    return airports_by_name


def _load_nav_segments(air_space: AirSpace, segments_path: PathLike) -> None:
    """Add every segment of the file whose two points exist in ``air_space``."""
    skipped_segments: List[str] = []

    for record in _read_records(segments_path, MIN_NAV_SEGMENT_FIELDS):
        origin_id, destination_id, cost = record.fields[:3]
        with _line_context(segments_path, record.line_number):
            was_added = air_space.add_segment(origin_id, destination_id, cost)
        if not was_added:
            skipped_segments.append(
                f"{origin_id}->{destination_id} (line {record.line_number})"
            )

    _log_data_warning(
        segments_path, "segments skipped because a point id does not exist", skipped_segments
    )


def _register_airports(
    air_space: AirSpace,
    airport_names: Sequence[str],
    airports_by_name: Dict[str, List[NavAirport]],
    airports_path: PathLike,
) -> None:
    """Register airports in the order their names appear in the airports file."""
    unmatched_names: List[str] = []

    for name in airport_names:
        matching_airports = airports_by_name.get(name)
        if not matching_airports:
            unmatched_names.append(name)
            continue
        for airport in matching_airports:
            air_space.add_airport(airport)

    # INFO and not WARNING: such a file may legitimately list names that are
    # not navigation points, and a warning on every load would just be noise.
    if unmatched_names:
        logger.info(
            "%s: %d listed names have no matching navigation point and were ignored.",
            _file_label(airports_path),
            len(unmatched_names),
        )


# --------------------------------------------------------------------------
# Low-level helpers
# --------------------------------------------------------------------------

def _read_records(file_path: PathLike, min_fields: int) -> List[DataRecord]:
    """Read a whitespace-separated text file into records.

    One function replaces the open/readline/strip/split loop that used to be
    copied for each of the five files. It also fixes the original behavior of
    stopping at the first blank line, and always closes the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        DataFileFormatError: If a line has fewer than ``min_fields`` fields or
            the file is not valid text in ``DATA_FILE_ENCODING``.
    """
    records: List[DataRecord] = []
    try:
        with open(file_path, "r", encoding=DATA_FILE_ENCODING) as data_file:
            for line_number, raw_line in enumerate(data_file, start=1):
                fields = raw_line.split()
                if not fields:
                    continue
                if len(fields) < min_fields:
                    raise _format_error(
                        file_path,
                        line_number,
                        f"expected at least {min_fields} fields, found {len(fields)}.",
                    )
                records.append(DataRecord(line_number, fields))
    except UnicodeDecodeError as error:
        raise DataFileFormatError(
            f"{_file_label(file_path)} could not be read as text ({error.reason}). "
            "If it uses a different encoding, change DATA_FILE_ENCODING in data_loader.py."
        ) from error
    return records


@contextmanager
def _line_context(file_path: PathLike, line_number: int) -> Iterator[None]:
    """Turn a ``ValueError`` raised while handling one line into a located error.

    Model classes report problems like "latitude out of range" without knowing
    where the data came from. Wrapping them here adds the file name and line
    number, which is what a person fixing a large data file actually needs.
    """
    try:
        yield
    except ValueError as error:
        raise _format_error(file_path, line_number, str(error)) from error


def _format_error(
    file_path: PathLike, line_number: int, problem: str
) -> DataFileFormatError:
    """Build the error describing ``problem`` at a given line of a file."""
    return DataFileFormatError(f"{_file_label(file_path)}, line {line_number}: {problem}")


def _file_label(file_path: PathLike) -> str:
    """Return just the file name, which is enough for messages to the user."""
    return os.path.basename(os.fspath(file_path))


def _log_data_warning(
    file_path: PathLike, summary: str, details: Sequence[str]
) -> None:
    """Log one aggregated warning with a few examples, if there is anything to report."""
    if not details:
        return

    shown = ", ".join(details[:MAX_REPORTED_PROBLEMS])
    hidden_count = len(details) - MAX_REPORTED_PROBLEMS
    more = f", ... and {hidden_count} more" if hidden_count > 0 else ""
    logger.warning(
        "%s: %s (%d): %s%s",
        _file_label(file_path),
        summary,
        len(details),
        shown,
        more,
    )
