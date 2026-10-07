# Import necessary modules and functions from custom libraries
from KMLwrite import *
from airSpace import *
import os

# Path to the directory where this script is saved (.../Final Project/Scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one folder to 'Project', then into 'Data' (.../FProject/Data)
data_dir = os.path.abspath(os.path.join(script_dir, "..", "Data"))

# Define the mode, which dictates the type of graph to be handled
mode = "o"  # o: empty, s: simple graph, c: complex graph

# Initialize the AirSpace and Graph objects
air = AirSpace()
Graph = graph([], [])  # This is for the simple graph
G = graph([], [])      # This is for the AirSpace graph

# Define geographical boundaries for different maps
EUROPElatlon = ['cyl', -5.2, 38, 5.1, 48.1, 'l']
ESPlatlon = ['cyl', -9, 36.2, 4.5, 43.5, 'l']
CATlatlon = ['cyl', -1.5, 38, 4.5, 42, 'h']
modeMAP = ""

# Main program loop
try:
    while True:
        # Display the main menu and get the user's choice
        option = str(input("""            
        MAIN MENU
        ===================================================================
        Select one of the options with its corresponding letter:
        a - Load simple graph (similar to the first week graph)
        b - Plot graph
        c - Plot node
        d - Plot path (List of Nodes end to finish)
        e - Plot minimum path
        -------------------------------------------------------------------
        f - Load airspace (Prefix)
        g - Plot airspace
        h - List airports
        i - Create airports.kml
        j - Create airspace.kml
        k - Create route.kml
        l - Find a route between 2 airports and plot it
        m - Open Google Earth and see path (needs .kml)
        n - Open Google Earth and see Airports (needs .kml)
        o - Open Google Earth and see Airspace (needs .kml)
        -------------------------------------------------------------------
        y - Empty current graph and deload file/files
        z - Exit

        Option: """))

        # Exit the program
        if option == "z":
            print("Selected option: Exit")
            break

        # Empty the current graph and deload files
        elif option == "y":
            print("Selected option: Empty current graph and deload file/files")
            try:
                Graph1 = graph([], [])
                Graph = Graph1  # This is for the simple graph
                G1 = graph([], [])
                G = G1  # This is for the AirSpace graph
                air = AirSpace()
                if mode == "s" or mode == "c":
                    plt.close()
                    modeMAP = ""
                else:
                    print("Nothing loaded yet")
                    mode = "o"
            except UnboundLocalError:
                print("Nothing loaded yet")

        # Load a simple graph from files
        elif option == "a":
            try:
                mode = "s"
                print("Selected option: Load simple graph (similar to the first week graph)")
                filename1 = str(input("Enter the points filename (.txt): "))  # Example: 1points.txt
                filename2 = str(input("Enter the segments filename (.txt): "))  # Example: 1segments.txt
                # Build full absolute paths to the Data folder
                path_points = os.path.join(data_dir, filename1)
                path_segments = os.path.join(data_dir, filename2)
                with open(path_points, "r") as F:
                    for line in F:
                        trozos = line.strip().split(" ")
                        n = Node(str(trozos[0]), float(trozos[1]), float(trozos[2]))  # (name, x, y)
                        Graph.nodesList.append(n)
                with open(path_segments, "r") as F:
                    for line in F:
                        trozos = line.strip().split(" ")
                        n1 = n2 = None
                        for node in Graph.nodesList:
                            if node.name == trozos[0]:
                                n1 = node
                            elif node.name == trozos[1]:
                                n2 = node
                        s = segment(n1, n2, float(trozos[2]))
                        Graph.segmentsList.append(s)
            except FileNotFoundError:
                print("Sorry, file not found")

        # Plot the loaded graph
        elif option == "b":
            mode = "s"
            if Graph.nodesList:
                print("Selected option: Plot graph")
                plot(Graph)
            else:
                print("Empty graph, load something before!")

        # Plot a specific node
        elif option == "c":
            mode = "s"
            if Graph.nodesList:
                print("Selected option: Plot node (ask node name)")
                NodeName = str(input("Name of the node to plot: "))
                plotNode(Graph, NodeName)
            else:
                print("Empty graph, load something before!")

        # Plot a path consisting of a list of nodes
        elif option == "d":
            try:
                mode = "s"
                path = []
                print("Selected option: Plot path (ask list of nodes to form the path)")
                lastNodeName = str(input("Enter a node to start the path: "))
                lastNode = next((node for node in Graph.nodesList if node.name == lastNodeName), None)
                if lastNode:
                    path.append(lastNode)
                    while True:
                        print(f"Available nodes: {[node.name for node in lastNode.nList]}")
                        nextNodeName = str(input("Next node ('z' to finish): "))
                        if nextNodeName == "z":
                            break
                        nextNode = next((node for node in lastNode.nList if node.name == nextNodeName), None)
                        if nextNode:
                            path.append(nextNode)
                            lastNode = nextNode
                        else:
                            print("Invalid node, try again.")
                    print(f"Final path: {[node.name for node in path]}")
                    plot_path(Graph, path)
            except AttributeError:
                print("Not a neighbour")

        # Plot the minimum path between two nodes using the A* algorithm
        elif option == "e":
            mode = "s"
            print("Selected option: Plot minimum path (ask origin node and destination node)")
            start_node = str(input("Origin node: "))
            goal_node = str(input("Destination node: "))
            if any(node.name == start_node for node in Graph.nodesList) and \
                    any(node.name == goal_node for node in Graph.nodesList):
                path = a_star(start_node, goal_node, Graph)
                if path:
                    print("Total Path:", [node.name for node in path])
                    plot_path(Graph, path)
                else:
                    print("No possible path")
            else:
                print("At least one of the nodes is not in the list")

        # Load airspace data from files
        elif option == "f":
            mode = "c"
            print("Selected option: Load airspace")
            try:
                filenameMain = str(input("Enter the name of the prefix (Cat, Spain or ECAC): "))
                filename1 = f"{filenameMain}_nav.txt"
                filename2 = f"{filenameMain}_seg.txt"
                filename3 = f"{filenameMain}_aer.txt"
                # Build full absolute paths to the Data folder
                path_nav = os.path.join(data_dir, filename1)
                path_seg = os.path.join(data_dir, filename2)
                path_aer = os.path.join(data_dir, filename3)
                loadAirspace(air, path_nav, path_seg, path_aer)
                if filenameMain == "Cat":
                    modeMAP = "CAT"
                elif filenameMain == "Spain":
                    modeMAP = "ESP"
                elif filenameMain == "ECAC":
                    modeMAP = "EUR"
                G = buildAirGraph(air)
            except FileNotFoundError:
                print("File not found")

        # Plot the loaded airspace graph
        elif option == "g":
            mode = "c"
            print("Selected option: Plot airspace")
            try:
                if modeMAP == "CAT":
                    coord = CATlatlon
                elif modeMAP == "ESP":
                    coord = ESPlatlon
                elif modeMAP == "EUR":
                    coord = EUROPElatlon
                else:
                    print("No Airspace loaded!")
                    continue
                plotAirSpaceGraph(G, coord)
            except UnboundLocalError:
                print("No Airspace loaded!")

        # List all airports in the airspace
        elif option == "h":
            print("Selected option: List airports")
            if mode == "c":
                for airport in air.navAirportList:
                    print(airport.name)
            else:
                print("Nothing loaded!")

        # Create a KML file for airports
        elif option == "i":
            mode = "c"
            print("Selected option: Create airports.kml file")
            filename_airports = str(input("Enter the name of the file (.kml): "))
            PointsToKML(air.navAirportList, filename_airports)

        # Create a KML file for the airspace
        elif option == "j":
            mode = "c"
            print("Selected option: Create airspace.kml file")
            filename_AirSpace = str(input("Enter the name of the file (.kml): "))
            PointsToKML(air.navPointList, filename_AirSpace)

        # Create a KML file for a specific route
        elif option == "k":
            mode = "c"
            try:
                print("Selected option: Create a route set of .kml files")
                filename_route = str(input("Enter the file name (.kml): "))
                PathToKML(path, filename_route)
            except TypeError:
                print("Empty path. Unable to create a route")

        # Find a route between two airports and plot it
        elif option == "l":
            mode = "c"
            if modeMAP == "CAT":
                coord = CATlatlon
            elif modeMAP == "ESP":
                coord = ESPlatlon
            elif modeMAP == "EUR":
                coord = EUROPElatlon
            print("Selected option: Find a route between 2 airports and plot it")
            NavOrg = str(input("Navigation point of origin: "))
            NavEnd = str(input("Navigation point to end: "))
            G = buildAirGraph(air)
            found1 = any(node.name == NavOrg for node in G.nodesList)
            found2 = any(node.name == NavEnd for node in G.nodesList)
            if found1 and found2:
                path = a_star(NavOrg, NavEnd, G)
                if path:
                    print("Total path:", [node.name for node in path])
                    print(f"Total distance travelled: {totalCost(path)}Km")
                    plot_pathMap(G, path, coord)
                else:
                    print("No path found")
            else:
                print("At least one of the navigation points is not in the graph")

        # Open Google Earth to view the path
        elif option == "m":
            mode = "c"
            print("Selected option: Open Google Earth and see path")
            os.startfile(filename_route)

        # Open Google Earth to view airports
        elif option == "n":
            mode = "c"
            print("Selected option: Open Google Earth and see Airports")
            os.startfile(filename_airports)

        # Open Google Earth to view airspace
        elif option == "o":
            mode = "c"
            print("Selected option: Open Google Earth and see Airspace")
            os.startfile(filename_AirSpace)

        # Handle invalid options
        else:
            print('Not a valid value. Try again')

# Handle potential exceptions
except ValueError:
    print("Not a valid value")
except FileNotFoundError:
    print("File not found")