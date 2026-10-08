"""Interactive console menu of the airspace project.

Only user interaction lives here: prompts, messages and the wiring between each
menu option and the module that does the real work (loading, path-finding,
plotting, KML export).

Design notes compared with the original script:

* Everything the menu remembers between options is kept in one
  :class:`MenuSession` object instead of loose global variables (``mode``,
  ``modeMAP``, ``path``, ``filename_route``...). The old ``mode`` flag was set
  by options even when nothing was loaded; the real state is now checked.
* Every option is a small function registered in one table, which is also used
  to print the menu, so the two can never get out of sync.
* Errors are handled per option. Previously the ``try`` wrapped the whole loop,
  so a single invalid input ended the program.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from functools import partial
from typing import Callable, Dict, Optional, Tuple

import plotting
from air_space import AirSpace
from data_loader import load_airspace_by_prefix, load_simple_graph
from graph import Graph
from kml_writer import write_points_kml, write_route_kml
from pathfinding import Route, find_shortest_path

logger = logging.getLogger(__name__)

# The "Data" folder lives next to the folder containing this script.
DEFAULT_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Data")
)

# Airspace file prefix -> map region used to draw it.
AIRSPACE_REGIONS: Dict[str, plotting.MapRegion] = {
    "Cat": plotting.CATALONIA,
    "Spain": plotting.SPAIN,
    "ECAC": plotting.EUROPE,
}

EXIT_KEY = "z"
PATH_FINISH_KEY = "z"  # Typed to stop adding nodes to a manually built path.
MENU_WIDTH = 67

# Keys of the KML files remembered by the session.
KML_ROUTE = "route"
KML_AIRPORTS = "airports"
KML_AIRSPACE = "airspace"


class MenuUsageError(Exception):
    """An option cannot run right now (nothing loaded, bad name...).

    Raised by option handlers and shown to the user as a plain message, which
    removes the repeated ``if ...: print(...) else: ...`` blocks of the
    original.
    """


@dataclass
class MenuSession:
    """Everything the menu remembers between options.

    Attributes:
        data_dir: Folder the data files are read from.
        simple_graph: Graph loaded by option "a".
        air_space: Airspace loaded by option "f".
        air_graph: Graph built once from ``air_space`` and reused by every
            airspace option (the original rebuilt it for each route search).
        map_region: Map area matching the loaded airspace.
        last_airspace_route: Most recent route found by option "l"; the source
            for the route KML export.
        kml_paths: Last file written for each KML kind.
    """

    data_dir: str
    simple_graph: Graph = field(default_factory=Graph)
    air_space: AirSpace = field(default_factory=AirSpace)
    air_graph: Graph = field(default_factory=Graph)
    map_region: Optional[plotting.MapRegion] = None
    last_airspace_route: Optional[Route] = None
    kml_paths: Dict[str, str] = field(default_factory=dict)

    @property
    def is_airspace_loaded(self) -> bool:
        """True when an airspace and its map region are available."""
        return not self.air_space.is_empty and self.map_region is not None

    def reset(self) -> None:
        """Forget every loaded graph and route (generated KML files stay on disk)."""
        self.simple_graph = Graph()
        self.air_space = AirSpace()
        self.air_graph = Graph()
        self.map_region = None
        self.last_airspace_route = None


@dataclass(frozen=True)
class MenuOption:
    """One entry of the menu: its key, its description and what it does."""

    key: str
    description: str
    handler: Callable[[MenuSession], None]


# --------------------------------------------------------------------------
# Small prompt / validation helpers
# --------------------------------------------------------------------------

def _prompt(text: str) -> str:
    """Ask the user for a line of text, without surrounding whitespace."""
    return input(text).strip()


def _prompt_required(text: str) -> str:
    """Ask for a value and refuse an empty answer."""
    answer = _prompt(text)
    if not answer:
        raise MenuUsageError("This value cannot be empty.")
    return answer


def _require_simple_graph(session: MenuSession) -> Graph:
    """Return the simple graph, or explain that none is loaded."""
    if session.simple_graph.is_empty:
        raise MenuUsageError("Empty graph, load something before!")
    return session.simple_graph


def _require_airspace(session: MenuSession) -> None:
    """Make sure an airspace is loaded, or explain that none is."""
    if not session.is_airspace_loaded:
        raise MenuUsageError("No Airspace loaded!")


def _match_airspace_prefix(typed_prefix: str) -> str:
    """Return the known prefix matching what the user typed, ignoring case.

    Using the canonical spelling keeps the data file names correct on systems
    where file names are case sensitive.
    """
    for known_prefix in AIRSPACE_REGIONS:
        if known_prefix.lower() == typed_prefix.lower():
            return known_prefix
    raise MenuUsageError(
        f"Unknown airspace '{typed_prefix}'. Choose one of: {', '.join(AIRSPACE_REGIONS)}."
    )


# --------------------------------------------------------------------------
# Simple graph options
# --------------------------------------------------------------------------

def _load_simple_graph(session: MenuSession) -> None:
    points_name = _prompt_required("Enter the points filename (.txt): ")
    segments_name = _prompt_required("Enter the segments filename (.txt): ")

    session.simple_graph = load_simple_graph(
        os.path.join(session.data_dir, points_name),
        os.path.join(session.data_dir, segments_name),
    )
    graph = session.simple_graph
    print(f"Loaded {len(graph.nodes)} nodes and {len(graph.segments)} segments.")


def _plot_simple_graph(session: MenuSession) -> None:
    plotting.plot_graph(_require_simple_graph(session))


def _plot_node(session: MenuSession) -> None:
    graph = _require_simple_graph(session)
    node_name = _prompt_required("Name of the node to plot: ")
    plotting.plot_node_neighbors(graph, node_name)


def _plot_manual_path(session: MenuSession) -> None:
    graph = _require_simple_graph(session)
    start_name = _prompt_required("Enter a node to start the path: ")
    start_node = graph.find_node(start_name)
    if start_node is None:
        raise MenuUsageError(f"Node '{start_name}' does not exist.")

    route = Route([start_node])
    while True:
        last_node = route.destination
        if not last_node.neighbors:
            print("No further nodes are reachable from here; the path ends.")
            break

        print(f"Available nodes: {[node.name for node in last_node.neighbors]}")
        answer = _prompt(f"Next node ('{PATH_FINISH_KEY}' to finish): ")
        if answer == PATH_FINISH_KEY:
            break

        next_node = next((node for node in last_node.neighbors if node.name == answer), None)
        if next_node is None:
            print("Invalid node, try again.")
            continue
        route.add_node(next_node)

    print(f"Final path: {route.names}")
    plotting.plot_route(graph, route)


def _plot_shortest_path(session: MenuSession) -> None:
    graph = _require_simple_graph(session)
    origin_name = _prompt_required("Origin node: ")
    destination_name = _prompt_required("Destination node: ")

    route = find_shortest_path(graph, origin_name, destination_name)
    if route is None:
        print("No possible path")
        return

    print("Total Path:", route.names)
    plotting.plot_route(graph, route)


# --------------------------------------------------------------------------
# Airspace options
# --------------------------------------------------------------------------

def _load_airspace(session: MenuSession) -> None:
    choices = ", ".join(AIRSPACE_REGIONS)
    prefix = _match_airspace_prefix(
        _prompt_required(f"Enter the name of the prefix ({choices}): ")
    )

    air_space = load_airspace_by_prefix(session.data_dir, prefix)

    # Only replace the session state once loading has fully succeeded.
    session.air_space = air_space
    session.air_graph = air_space.build_graph()
    session.map_region = AIRSPACE_REGIONS[prefix]
    session.last_airspace_route = None
    print(
        f"Loaded {len(air_space.nav_points)} navigation points, "
        f"{len(air_space.nav_segments)} segments and {len(air_space.airports)} airports."
    )


def _plot_airspace(session: MenuSession) -> None:
    _require_airspace(session)
    plotting.plot_airspace_map(session.air_graph, session.map_region)


def _list_airports(session: MenuSession) -> None:
    if session.air_space.is_empty:
        raise MenuUsageError("Nothing loaded!")
    if not session.air_space.airports:
        print("This airspace has no airports.")
        return
    for airport in session.air_space.airports:
        print(airport.name)


def _find_and_plot_airspace_route(session: MenuSession) -> None:
    _require_airspace(session)
    origin_name = _prompt_required("Navigation point of origin: ")
    destination_name = _prompt_required("Navigation point to end: ")

    route = find_shortest_path(session.air_graph, origin_name, destination_name)
    if route is None:
        print("No path found")
        return

    # Remembered before plotting, so the route can still be exported to KML
    # even if the map cannot be drawn (for example without Basemap installed).
    session.last_airspace_route = route
    print("Total path:", route.names)
    print(f"Total distance travelled: {route.great_circle_length_km():.2f} km")
    plotting.plot_route_on_map(session.air_graph, route, session.map_region)


# --------------------------------------------------------------------------
# KML options
# --------------------------------------------------------------------------

def _create_airports_kml(session: MenuSession) -> None:
    _require_airspace(session)
    if not session.air_space.airports:
        raise MenuUsageError("This airspace has no airports to export.")
    file_name = _prompt_required("Enter the name of the file (.kml): ")
    _remember_kml(session, KML_AIRPORTS, write_points_kml(session.air_space.airports, file_name))


def _create_airspace_kml(session: MenuSession) -> None:
    _require_airspace(session)
    file_name = _prompt_required("Enter the name of the file (.kml): ")
    _remember_kml(session, KML_AIRSPACE, write_points_kml(session.air_space.nav_points, file_name))


def _create_route_kml(session: MenuSession) -> None:
    if session.last_airspace_route is None:
        raise MenuUsageError("Empty path. Find a route first (option 'l') to create its .kml.")
    file_name = _prompt_required("Enter the file name (.kml): ")
    _remember_kml(session, KML_ROUTE, write_route_kml(session.last_airspace_route, file_name))


def _remember_kml(session: MenuSession, kml_key: str, written_path: str) -> None:
    """Store the path of a freshly written KML file and tell the user where it is."""
    session.kml_paths[kml_key] = written_path
    print(f"Created {os.path.abspath(written_path)}")


def _open_generated_kml(session: MenuSession, kml_key: str, creating_option: str) -> None:
    """Open a KML file created earlier in the session with the default application."""
    kml_path = session.kml_paths.get(kml_key)
    if kml_path is None:
        raise MenuUsageError(
            f"No {kml_key} .kml file has been created yet. Use option '{creating_option}' first."
        )
    if not os.path.exists(kml_path):
        raise MenuUsageError(f"{kml_path} no longer exists. Create it again with option '{creating_option}'.")
    _open_with_default_application(kml_path)


def _open_with_default_application(file_path: str) -> None:
    """Open a file with the application the operating system associates with it.

    The original used ``os.startfile``, which only exists on Windows and made
    the program crash everywhere else.

    Raises:
        MenuUsageError: If the file could not be opened.
    """
    absolute_path = os.path.abspath(file_path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(absolute_path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", absolute_path], check=True)
        else:
            subprocess.run(["xdg-open", absolute_path], check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise MenuUsageError(f"Could not open {absolute_path}: {error}") from error


# --------------------------------------------------------------------------
# Session options
# --------------------------------------------------------------------------

def _reset_session(session: MenuSession) -> None:
    if session.simple_graph.is_empty and session.air_space.is_empty:
        print("Nothing loaded yet")
        return
    session.reset()
    plotting.close_all_plots()
    print("Everything has been unloaded.")


# --------------------------------------------------------------------------
# Menu table and main loop
# --------------------------------------------------------------------------

# Options grouped as they are displayed; a separator line is printed between groups.
MENU_GROUPS: Tuple[Tuple[MenuOption, ...], ...] = (
    (
        MenuOption("a", "Load simple graph (similar to the first week graph)", _load_simple_graph),
        MenuOption("b", "Plot graph", _plot_simple_graph),
        MenuOption("c", "Plot node", _plot_node),
        MenuOption("d", "Plot path (List of Nodes end to finish)", _plot_manual_path),
        MenuOption("e", "Plot minimum path", _plot_shortest_path),
    ),
    (
        MenuOption("f", "Load airspace (Prefix)", _load_airspace),
        MenuOption("g", "Plot airspace", _plot_airspace),
        MenuOption("h", "List airports", _list_airports),
        MenuOption("i", "Create airports.kml", _create_airports_kml),
        MenuOption("j", "Create airspace.kml", _create_airspace_kml),
        MenuOption("k", "Create route.kml", _create_route_kml),
        MenuOption("l", "Find a route between 2 airports and plot it", _find_and_plot_airspace_route),
        MenuOption("m", "Open Google Earth and see path (needs .kml)",
                   partial(_open_generated_kml, kml_key=KML_ROUTE, creating_option="k")),
        MenuOption("n", "Open Google Earth and see Airports (needs .kml)",
                   partial(_open_generated_kml, kml_key=KML_AIRPORTS, creating_option="i")),
        MenuOption("o", "Open Google Earth and see Airspace (needs .kml)",
                   partial(_open_generated_kml, kml_key=KML_AIRSPACE, creating_option="j")),
    ),
    (
        MenuOption("y", "Empty current graph and deload file/files", _reset_session),
    ),
)

OPTIONS_BY_KEY: Dict[str, MenuOption] = {
    option.key: option for group in MENU_GROUPS for option in group
}


def build_menu_text() -> str:
    """Return the menu as text, generated from ``MENU_GROUPS``."""
    heavy_line = "=" * MENU_WIDTH
    light_line = "-" * MENU_WIDTH

    lines = [
        "",
        "MAIN MENU",
        heavy_line,
        "Select one of the options with its corresponding letter:",
    ]
    for group_index, group in enumerate(MENU_GROUPS):
        if group_index > 0:
            lines.append(light_line)
        lines.extend(f"{option.key} - {option.description}" for option in group)
    lines.append(f"{EXIT_KEY} - Exit")
    lines.append("")
    return "\n".join(lines)


def run_option(session: MenuSession, option: MenuOption) -> None:
    """Run one menu option, turning expected failures into friendly messages.

    The menu keeps running after any error: one bad file name or one unknown
    node must not end the session.
    """
    try:
        option.handler(session)
    except MenuUsageError as error:
        print(error)
    except FileNotFoundError as error:
        print(f"File not found: {error.filename}")
    except (ValueError, ImportError, OSError) as error:
        # ValueError also covers DataFileFormatError and invalid user input.
        print(f"Error: {error}")
    except Exception:  # noqa: BLE001 - last resort so a bug cannot kill the menu
        logger.exception("Unexpected error while running option '%s'", option.key)
        print("Unexpected error (details above). The menu is still running.")


def run_menu(session: Optional[MenuSession] = None) -> None:
    """Show the menu repeatedly until the user chooses to exit."""
    session = session or MenuSession(data_dir=DEFAULT_DATA_DIR)
    menu_text = build_menu_text()

    try:
        while True:
            print(menu_text)
            choice = _prompt("Option: ").lower()

            if choice == EXIT_KEY:
                print("Selected option: Exit")
                return

            option = OPTIONS_BY_KEY.get(choice)
            if option is None:
                print("Not a valid value. Try again")
                continue

            print(f"Selected option: {option.description}")
            run_option(session, option)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C or a closed input stream: leave quietly instead of a traceback.
        print("\nInterrupted. Exiting.")


def main() -> None:
    """Program entry point."""
    # Plain messages so data-loading warnings read naturally in the console.
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    run_menu()


if __name__ == "__main__":
    main()
