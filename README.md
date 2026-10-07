# Airspace Route Planner

A Python-based airspace route planning tool that models airspace as a graph and uses the A* algorithm to find optimal routes between navigation points. The project also provides visualization of airspace structures and planned routes, with support for KML generation for visualization in Google Earth.

## Overview

This project was developed as an airspace route planning application using real-world-style navigation data for different geographic areas.

The airspace is represented as a graph composed of navigation points and segments. The A* pathfinding algorithm is then used to determine a route between selected points while considering the distance between nodes.

The application includes graphical visualization of airspace networks and routes using Matplotlib and Basemap, as well as KML generation for external visualization.

## Features

- Airspace graph construction from navigation data
- A* pathfinding algorithm for route planning
- Distance-based pathfinding heuristic
- Route visualization using Matplotlib
- Geographic visualization using Basemap
- KML generation for visualization in Google Earth
- Support for different airspace datasets, including Catalonia, Spain and ECAC
- Navigation point, segment and airport data processing

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
│   ├── airSpace.py
│   ├── graph.py
│   ├── KMLwrite.py
│   ├── navAirport.py
│   ├── navPoint.py
│   ├── navSegment.py
│   ├── node.py
│   ├── path.py
│   ├── project_menu.py
│   └── segment.py
│
├── .gitignore
├── requirements.txt
└── README.md

## A* Pathfinding

The route planner represents the airspace network as a graph and uses the A* algorithm to search for a path between two navigation points.

The implementation maintains:

- `g` scores representing the cost from the starting node
- `f` scores combining the current path cost with the heuristic estimate
- A set of nodes to be evaluated
- A predecessor structure for reconstructing the final route

The heuristic is based on the distance between navigation points.

## Data

The `Data/` directory contains the navigation datasets used by the application.

Available datasets include:

- Catalonia
- Spain
- ECAC
- Additional point and segment datasets

These files provide the navigation points, segments and airport-related data used to construct the airspace graph.

## Requirements

- Python 3.12 or compatible Python 3 version
- NumPy
- Matplotlib
- Basemap
- adjustText

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

## Visualization

The project uses Matplotlib and Basemap to visualize airspace structures and calculated routes geographically.

Routes can also be exported to KML format and visualized using Google Earth.

## Technologies

- Python
- A* Pathfinding
- Graph Algorithms
- NumPy
- Matplotlib
- Basemap
- adjustText
- KML

## Project Context

This project was developed as an aerospace engineering project focused on airspace modelling, route planning and algorithmic pathfinding.