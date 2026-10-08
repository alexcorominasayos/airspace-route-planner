# Airspace Route Planner

A Python-based airspace route planning tool that models airspace as a graph and uses the A* algorithm to find optimal routes between navigation points. The project also provides visualization of airspace structures and planned routes, with support for KML generation for visualization in Google Earth.

## Overview

This project was developed as an airspace route planning application using real-world-style navigation data for different geographic areas.

The airspace is represented as a graph composed of navigation points and segments. The A* pathfinding algorithm is then used to determine a route between selected points while considering the distance between nodes.

The application includes graphical visualization of airspace networks and routes using Matplotlib and Basemap, as well as KML generation for external visualization.

The code is organized into small modules with a single responsibility each (data model, algorithms, file input/output, plotting and user interface). See [Architecture](#architecture) for details.

## Features

- Airspace graph construction from navigation data, with validated file loading (errors report the file name and line number)
- A* pathfinding algorithm for route planning, backed by a priority queue
- Distance-based pathfinding heuristic
- Route visualization using Matplotlib
- Geographic visualization using Basemap
- KML generation for visualization in Google Earth (airports, navigation points and routes with an animated track)
- Support for different airspace datasets, including Catalonia, Spain and ECAC
- Navigation point, segment and airport data processing
- Interactive console menu that stays running when an input or a file is invalid

## Project Structure

```text
.
├── Data/
│   ├── 1points.txt
│   ├── 1segments.txt
│   ├── Cat_aer.txt
│   ├── Cat_nav.txt
│   ├── Cat_seg.txt
│   ├── Spain_aer.txt
│   ├── Spain_nav.txt
│   ├── Spain_seg.txt
│   ├── ECAC_aer.txt
│   ├── ECAC_nav.txt
│   └── ECAC_seg.txt
│
├── Scripts/
│   ├── air_space.py
│   ├── data_loader.py
│   ├── geometry.py
│   ├── graph.py
│   ├── kml_writer.py
│   ├── nav_airport.py
│   ├── nav_point.py
│   ├── node.py
│   ├── pathfinding.py
│   ├── plotting.py
│   ├── project_menu.py
│   └── segment.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

## Architecture

Each module in `Scripts/` has one responsibility. A module only imports modules listed above it in the table, so there are no circular imports, and the data classes can be used without Matplotlib or Basemap.

| Layer | Module | Responsibility |
|---|---|---|
| Foundations | `geometry.py` | Euclidean and haversine (great-circle) distances, and geographic coordinate validation |
| Data model | `node.py` | `Node`: a named point on a plane that keeps its list of neighbors |
| | `segment.py` | `Segment`: a directed, weighted connection between two nodes |
| | `graph.py` | `Graph`: container of nodes and segments (data only, no plotting) |
| | `nav_point.py` | `NavPoint`: a `Node` with geographic coordinates (x is longitude, y is latitude) |
| | `nav_airport.py` | `NavAirport`: a `NavPoint` that also tracks its SIDs and STARs |
| | `air_space.py` | `AirSpace`: the navigation points, segments and airports of a region |
| Algorithms | `pathfinding.py` | `Route` and `find_shortest_path` (A*) |
| Input / output | `data_loader.py` | Reads the data files into `Graph` and `AirSpace` objects |
| | `kml_writer.py` | Exports points and routes to KML |
| | `plotting.py` | All Matplotlib and Basemap drawing |
| Interface | `project_menu.py` | Interactive console menu |

## A* Pathfinding

The route planner represents the airspace network as a graph and uses the A* algorithm to search for a path between two navigation points. It is implemented in `find_shortest_path` (`pathfinding.py`) and returns a `Route`, or `None` when the destination cannot be reached.

The implementation maintains:

- A dictionary with the cheapest known cost from the starting node (the `g` score) for every discovered node
- A priority queue ordered by the estimated total cost (`f = g + heuristic`), which decides the next node to evaluate
- A predecessor dictionary for reconstructing the final route

Using a heap and dictionaries, instead of repeated list searches, keeps the search fast on large airspaces such as ECAC.

The heuristic is based on the distance between navigation points. By default the same distance function is used both as the cost of moving between two nodes and as the estimate to the goal: the Euclidean distance between their coordinates. For geographic data this distance is measured in degrees, so the route found is the shortest one in degrees, while the total length shown to the user is computed afterwards in kilometres with the haversine formula. To make the search minimize real distances, pass a different distance function:

```python
from nav_point import NavPoint
from pathfinding import find_shortest_path

route = find_shortest_path(graph, "LEBL", "LEMD", distance=NavPoint.great_circle_distance_km_to)
```

## Data

The `Data/` directory contains the navigation datasets used by the application.

Available datasets include:

- Catalonia (`Cat`)
- Spain (`Spain`)
- ECAC (`ECAC`)
- Additional point and segment datasets (`1points.txt`, `1segments.txt`)

These files provide the navigation points, segments and airport-related data used to construct the airspace graph.

### File formats

Fields are separated by whitespace. Blank lines are ignored and extra trailing fields are skipped. Files are read as UTF-8 (this can be changed with the `DATA_FILE_ENCODING` constant in `data_loader.py`).

| File | One line contains |
|---|---|
| Simple graph points | `<name> <x> <y>` |
| Simple graph segments | `<origin name> <destination name> <cost>` |
| Airspace navigation points (`<prefix>_nav.txt`) | `<id> <name> <latitude> <longitude>` |
| Airspace segments (`<prefix>_seg.txt`) | `<origin id> <destination id> <cost>` |
| Airspace airports (`<prefix>_aer.txt`) | `<airport name>` |

Every navigation point whose name appears in the airports file is treated as an airport.

A malformed line stops the loading with an error that names the file and the line. A segment that refers to a point that does not exist is skipped, and a single warning with a few examples is printed.

## Requirements

- Python 3.12 or compatible Python 3 version
- Matplotlib (NumPy is installed automatically as one of its dependencies)
- Basemap, only needed for the map views (menu options `g` and `l`). The simple graph options work without it
- `basemap-data-hires`, needed for the high-resolution Catalonia map

## Installation

Install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run the main project menu:

```bash
python Scripts/project_menu.py
```

The application can then be used to load airspace data, select navigation points and calculate routes using the A* algorithm.

The menu is organized in three groups:

- `a` to `e`: load a simple graph, plot it, plot a node, plot a path and plot the minimum path
- `f` to `o`: load an airspace (`Cat`, `Spain` or `ECAC`), plot it, list its airports, find and plot a route, create the KML files and open them in Google Earth
- `y` unloads everything and `z` exits

## Visualization

The project uses Matplotlib and Basemap to visualize airspace structures and calculated routes geographically.

Routes can also be exported to KML format and visualized using Google Earth. The route file contains the route as a line, one placemark per stop and an animated track. KML files are saved in the directory from which the program is launched, and the menu prints the full path of each file it creates.

## Technologies

- Python
- A* Pathfinding
- Graph Algorithms
- Matplotlib
- Basemap
- KML

## Project Context

This project was developed as an aerospace engineering project focused on airspace modelling, route planning and algorithmic pathfinding.
