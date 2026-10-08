"""All matplotlib and Basemap drawing of the project.

Keeping every plot in this module has two benefits. The data classes never need
to import matplotlib, and the code that draws nodes, segments and routes exists
once. The original project copy-pasted it into four different plot functions,
each with slightly different hard-coded numbers; those numbers now live in the
:class:`DrawingStyle` presets below.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from graph import Graph
from pathfinding import Route

# Converts (x, y) data coordinates into the coordinates used to draw them.
# Flat graphs draw their coordinates as they are; maps need Basemap to project
# longitude/latitude first.
Projection = Callable[[float, float], Tuple[float, float]]

FIGURE_SIZE = (16, 10)
AXIS_MARGIN = 1.0  # Free space around the nodes of a flat graph, in data units.

# Default pauses (seconds) that make nodes, segments and route legs appear one
# after another, as the original plots did. Pass 0 to draw everything at once.
GRAPH_ANIMATION_PAUSE_SECONDS = 0.05
ROUTE_ANIMATION_PAUSE_SECONDS = 0.5
FINAL_REFRESH_SECONDS = 0.1

GRID_COLOR = "green"
GRID_LINE_STYLE = "--"
GRID_LINE_WIDTH = 0.5

ROUTE_COLOR = "red"
ROUTE_LINE_WIDTH = 2

LAND_COLOR = "#009344"
SEA_COLOR = "#85C7D5"
NODE_COLOR = "#FF5D5D"

VALID_MAP_RESOLUTIONS = ("c", "l", "i", "h", "f")


@dataclass(frozen=True)
class DrawingStyle:
    """Visual parameters shared by every node/segment drawing routine.

    Attributes:
        node_color: Color of the node markers.
        node_marker: Matplotlib marker symbol of the nodes.
        node_marker_size: Marker size in points.
        node_label_size: Font size of the node names.
        node_label_bold: Whether node names are drawn in bold.
        node_label_offset: Shift of the node name from its marker, in data units.
        arrow_color: Color of the segment arrows.
        arrow_head_width: Width of the arrow heads, in data units.
        arrow_width: Width of the arrow shafts, in data units.
        arrow_alpha: Opacity of the arrows (1 is fully opaque).
        cost_label_size: Font size of the cost shown on each segment.
        cost_label_offset: Shift of the cost label from the segment midpoint.
    """

    node_color: str
    node_marker: str
    node_marker_size: float
    node_label_size: float
    node_label_bold: bool
    node_label_offset: float
    arrow_color: str
    arrow_head_width: float
    arrow_width: float
    arrow_alpha: float
    cost_label_size: float
    cost_label_offset: float


# Presets reproducing the look of the original plot functions.
GRAPH_STYLE = DrawingStyle(
    node_color="black", node_marker="o", node_marker_size=6,
    node_label_size=10, node_label_bold=False, node_label_offset=0.3,
    arrow_color="r", arrow_head_width=0.3, arrow_width=0.001, arrow_alpha=1.0,
    cost_label_size=9, cost_label_offset=0.3,
)
NEIGHBORS_STYLE = replace(GRAPH_STYLE, node_color="gray")
ROUTE_GRAPH_STYLE = DrawingStyle(
    node_color=NODE_COLOR, node_marker="v", node_marker_size=6,
    node_label_size=10, node_label_bold=True, node_label_offset=0.3,
    arrow_color="grey", arrow_head_width=0.2, arrow_width=0.07, arrow_alpha=0.25,
    cost_label_size=10, cost_label_offset=0.2,
)
MAP_STYLE = DrawingStyle(
    node_color=NODE_COLOR, node_marker="v", node_marker_size=3,
    node_label_size=5, node_label_bold=True, node_label_offset=0.0,
    arrow_color="r", arrow_head_width=0.02, arrow_width=0.001, arrow_alpha=0.25,
    cost_label_size=5, cost_label_offset=0.005,
)
ROUTE_MAP_STYLE = replace(MAP_STYLE, arrow_color="grey", arrow_head_width=0.05)


@dataclass(frozen=True)
class MapRegion:
    """A rectangular geographic area to show on a Basemap map.

    This replaces the anonymous lists like ``['cyl', -5.2, 38, 5.1, 48.1, 'l']``
    and the code that guessed the map title by comparing one of their numbers.

    Attributes:
        name: Human-readable name used in plot titles.
        min_longitude: Western edge, in degrees.
        min_latitude: Southern edge, in degrees.
        max_longitude: Eastern edge, in degrees.
        max_latitude: Northern edge, in degrees.
        resolution: Basemap coastline detail: c(rude), l(ow), i(ntermediate),
            h(igh) or f(ull). Finer levels need extra Basemap data packages.
        projection: Basemap projection code.
    """

    name: str
    min_longitude: float
    min_latitude: float
    max_longitude: float
    max_latitude: float
    resolution: str = "l"
    projection: str = "cyl"

    def __post_init__(self) -> None:
        if self.min_longitude >= self.max_longitude:
            raise ValueError(f"Map region '{self.name}': min_longitude must be below max_longitude.")
        if self.min_latitude >= self.max_latitude:
            raise ValueError(f"Map region '{self.name}': min_latitude must be below max_latitude.")
        if self.resolution not in VALID_MAP_RESOLUTIONS:
            raise ValueError(
                f"Map region '{self.name}': resolution must be one of {VALID_MAP_RESOLUTIONS}, "
                f"got {self.resolution!r}."
            )


EUROPE = MapRegion("Europe", -5.2, 38, 5.1, 48.1, "l")
SPAIN = MapRegion("Spain", -9, 36.2, 4.5, 43.5, "l")
CATALONIA = MapRegion("Catalonia", -1.5, 38, 4.5, 42, "h")


# --------------------------------------------------------------------------
# Public plots
# --------------------------------------------------------------------------

def plot_graph(
    graph: Graph, pause_seconds: float = GRAPH_ANIMATION_PAUSE_SECONDS
) -> None:
    """Draw every node and segment of a flat graph in the current window.

    Args:
        graph: The graph to draw.
        pause_seconds: Delay after each node and segment so the graph builds up
            visibly. Use 0 to draw it instantly.

    Raises:
        ValueError: If the graph has no nodes.
    """
    _require_nodes(graph)
    ax = _reuse_current_axes()
    _draw_nodes(ax, graph, GRAPH_STYLE, _flat_plane, pause_seconds)
    _draw_segments(ax, graph, GRAPH_STYLE, _flat_plane, pause_seconds)
    _show(block=False)


def plot_node_neighbors(
    graph: Graph,
    node_name: str,
    pause_seconds: float = GRAPH_ANIMATION_PAUSE_SECONDS,
    block: bool = True,
) -> None:
    """Draw all nodes in gray and highlight the links from one node to its neighbors.

    Args:
        graph: The graph to draw.
        node_name: Name of the node whose outgoing links are highlighted.
        pause_seconds: Delay after each drawn element. Use 0 to draw instantly.
        block: If True (the original behavior) wait until the window is closed.

    Raises:
        ValueError: If the graph is empty or has no node called ``node_name``.
    """
    _require_nodes(graph)
    selected_node = graph.find_node(node_name)
    # Checked before touching the window: the original cleared and half-drew
    # the figure before discovering the node did not exist.
    if selected_node is None:
        raise ValueError(f"Node '{node_name}' is not in the graph.")

    ax = _reuse_current_axes()
    _draw_nodes(ax, graph, NEIGHBORS_STYLE, _flat_plane, pause_seconds)
    for neighbor in selected_node.neighbors:
        _draw_connection(
            ax, selected_node, neighbor, selected_node.distance_to(neighbor),
            NEIGHBORS_STYLE, _flat_plane,
        )
        _animate(pause_seconds)
    _show(block)


def plot_route(graph: Graph, route: Route, block: bool = True) -> None:
    """Draw a flat graph in a new window with a route highlighted on top.

    Args:
        graph: The graph to draw.
        route: The route to highlight.
        block: If True (the original behavior) wait until the window is closed.

    Raises:
        ValueError: If the graph has no nodes.
        TypeError: If ``route`` is not a Route.
    """
    _require_nodes(graph)
    _require_route(route)

    plt.ion()
    _, ax = plt.subplots(figsize=FIGURE_SIZE)
    _draw_nodes(ax, graph, ROUTE_GRAPH_STYLE, _flat_plane)
    _draw_segments(ax, graph, ROUTE_GRAPH_STYLE, _flat_plane)
    _draw_route(ax, route, _flat_plane)

    # Arrows do not take part in matplotlib's automatic scaling, so frame the
    # nodes explicitly to keep the arrows near the border visible.
    x_values = [node.x_coord for node in graph.nodes]
    y_values = [node.y_coord for node in graph.nodes]
    ax.set_xlim(min(x_values) - AXIS_MARGIN, max(x_values) + AXIS_MARGIN)
    ax.set_ylim(min(y_values) - AXIS_MARGIN, max(y_values) + AXIS_MARGIN)

    total_length = round(route.euclidean_length(), 2)
    ax.set_title(f"Best Path (Simple Graph), Total Distance: {total_length}")
    _show(block)


def plot_airspace_map(graph: Graph, region: MapRegion, block: bool = False) -> None:
    """Draw an airspace graph over a geographic map.

    Args:
        graph: Graph of navigation points (see ``AirSpace.build_graph``).
        region: Geographic area to show.
        block: If True wait until the window is closed.

    Raises:
        ValueError: If the graph has no nodes.
        ImportError: If the optional Basemap package is not installed.
    """
    _require_nodes(graph)
    ax, basemap = _create_map_axes(region)
    _draw_nodes(ax, graph, MAP_STYLE, basemap)
    _draw_segments(ax, graph, MAP_STYLE, basemap)
    ax.set_title(f"Map of {region.name}'s Airspace")
    _show(block)


def plot_route_on_map(
    graph: Graph,
    route: Route,
    region: MapRegion,
    pause_seconds: float = ROUTE_ANIMATION_PAUSE_SECONDS,
    block: bool = False,
) -> None:
    """Draw an airspace graph over a map and animate a route across it.

    Args:
        graph: Graph of navigation points.
        route: Route of navigation points to highlight.
        region: Geographic area to show.
        pause_seconds: Delay after each route leg. Use 0 to draw instantly.
        block: If True wait until the window is closed.

    Raises:
        ValueError: If the graph has no nodes.
        TypeError: If ``route`` is not a Route of navigation points.
        ImportError: If the optional Basemap package is not installed.
    """
    _require_nodes(graph)
    _require_route(route)
    # Computed first so a route of plain nodes fails before any window opens.
    total_km = round(route.great_circle_length_km(), 2)

    ax, basemap = _create_map_axes(region)
    _draw_nodes(ax, graph, ROUTE_MAP_STYLE, basemap)
    _draw_segments(ax, graph, ROUTE_MAP_STYLE, basemap)
    ax.set_title(f"Best Path (Map), Total Distance: {total_km} Km")
    _draw_route(ax, route, basemap, pause_seconds)
    _show(block)


def close_all_plots() -> None:
    """Close every open plot window."""
    plt.close("all")


# --------------------------------------------------------------------------
# Shared drawing helpers
# --------------------------------------------------------------------------

def _flat_plane(x_coord: float, y_coord: float) -> Tuple[float, float]:
    """Projection for flat graphs: coordinates are drawn exactly as they are."""
    return x_coord, y_coord


def _draw_nodes(
    ax: Axes, graph: Graph, style: DrawingStyle, project: Projection,
    pause_seconds: float = 0.0,
) -> None:
    """Draw a marker and a name label for every node of the graph."""
    for node in graph.nodes:
        x, y = project(node.x_coord, node.y_coord)
        ax.plot(
            x, y, color=style.node_color, marker=style.node_marker,
            markersize=style.node_marker_size, linestyle="none",
        )
        ax.text(
            x + style.node_label_offset, y + style.node_label_offset, node.name,
            fontsize=style.node_label_size, ha="center", va="center",
            weight="bold" if style.node_label_bold else "normal",
        )
        _animate(pause_seconds)


def _draw_segments(
    ax: Axes, graph: Graph, style: DrawingStyle, project: Projection,
    pause_seconds: float = 0.0,
) -> None:
    """Draw an arrow and a cost label for every segment of the graph."""
    for segment in graph.segments:
        _draw_connection(
            ax, segment.origin, segment.destination, segment.cost, style, project
        )
        _animate(pause_seconds)


def _draw_connection(
    ax: Axes, origin, destination, cost: float, style: DrawingStyle, project: Projection
) -> None:
    """Draw one directed arrow with its cost written next to its midpoint."""
    x1, y1 = project(origin.x_coord, origin.y_coord)
    x2, y2 = project(destination.x_coord, destination.y_coord)
    ax.arrow(
        x1, y1, x2 - x1, y2 - y1, head_width=style.arrow_head_width,
        length_includes_head=True, color=style.arrow_color,
        width=style.arrow_width, alpha=style.arrow_alpha,
    )
    ax.text(
        (x1 + x2) / 2 + style.cost_label_offset,
        (y1 + y2) / 2 + style.cost_label_offset,
        round(cost, 2), fontsize=style.cost_label_size, ha="center", va="center",
    )


def _draw_route(
    ax: Axes, route: Route, project: Projection, pause_seconds: float = 0.0
) -> None:
    """Draw the legs of a route as thick lines, one leg at a time."""
    for start, end in zip(route.nodes, route.nodes[1:]):
        x1, y1 = project(start.x_coord, start.y_coord)
        x2, y2 = project(end.x_coord, end.y_coord)
        ax.plot([x1, x2], [y1, y2], color=ROUTE_COLOR, linewidth=ROUTE_LINE_WIDTH)
        _animate(pause_seconds)


def _reuse_current_axes() -> Axes:
    """Clear the current window (opening one if needed) and return its axes.

    Reusing the window avoids opening a new one on every request, as the
    original ``plot`` and ``plotNode`` did.
    """
    plt.ion()
    plt.clf()
    plt.grid(color=GRID_COLOR, linestyle=GRID_LINE_STYLE, linewidth=GRID_LINE_WIDTH)
    return plt.gca()


def _create_map_axes(region: MapRegion) -> Tuple[Axes, "Basemap"]:  # noqa: F821
    """Open a new window showing the base map of ``region``.

    Returns:
        The axes to draw on and the Basemap object, which is also the function
        that converts (longitude, latitude) into drawing coordinates.
    """
    basemap_class = _import_basemap()

    plt.ion()
    _, ax = plt.subplots(figsize=FIGURE_SIZE)
    basemap = basemap_class(
        projection=region.projection,
        llcrnrlon=region.min_longitude, llcrnrlat=region.min_latitude,
        urcrnrlon=region.max_longitude, urcrnrlat=region.max_latitude,
        resolution=region.resolution, ax=ax,
    )
    basemap.drawcoastlines()
    basemap.drawcountries()
    # The original drew the map boundary twice (plain, then with the sea color);
    # once with the sea color is enough and gives the same picture.
    basemap.drawmapboundary(fill_color=SEA_COLOR)
    basemap.fillcontinents(color=LAND_COLOR, lake_color=SEA_COLOR)
    return ax, basemap


def _import_basemap():
    """Import Basemap on demand and explain how to install it if it is missing.

    Importing it lazily means the flat-graph features keep working on machines
    where this heavy optional package is not installed, instead of the whole
    program failing at start-up.
    """
    try:
        from mpl_toolkits.basemap import Basemap
    except ImportError as error:
        raise ImportError(
            "Map plots need the optional 'basemap' package. Install it with "
            "'pip install basemap' (and 'pip install basemap-data-hires' for "
            "the high-resolution Catalonia map)."
        ) from error
    return Basemap


def _animate(pause_seconds: float) -> None:
    """Refresh the window and wait, so drawing is visible step by step."""
    if pause_seconds > 0:
        plt.draw()
        plt.pause(pause_seconds)


def _show(block: bool) -> None:
    """Display the figure, optionally waiting until the user closes it."""
    plt.show(block=block)
    if not block:
        # Gives the window a moment to paint before control returns to the menu.
        plt.pause(FINAL_REFRESH_SECONDS)


def _require_nodes(graph: Graph) -> None:
    """Raise a clear error instead of failing later on min() of an empty list."""
    if graph.is_empty:
        raise ValueError("The graph has no nodes to plot.")


def _require_route(route: Route) -> None:
    """Make sure a Route object was passed, not a bare list or ``None``."""
    if not isinstance(route, Route):
        raise TypeError(f"Expected a Route, got {type(route).__name__}.")
