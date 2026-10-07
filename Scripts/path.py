from graph import *
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from adjustText import adjust_text

class path:
   def __init__(self,nodes,dist):
       self.nodes=nodes
       self.dist=dist
       if dist!=[]:
        self.totalCost=dist[-1]


def addNodeToPath(G, P, nameNode):
   n=0
   while n<len(G.nodesList):
       if nameNode==G.nodesList[n].name:
           Node1=G.nodesList[n]
       n=n+1
   i=0
   Viable=False
   while i<len(G.nodesList):
       if nameNode==G.nodesList[i].name:
           j=0
           while j<len(G.nodesList[i-1].nList):
               if nameNode==G.nodesList[i-1].nList[j].name:
                   Viable=True
                   P.nodes.append(Node1)
               j=j+1
       i=i+1
   return Viable

def totalCost(path):
    totalDistance = 0
    i=0
    while i<(len(path)-1):
        rE = 6370000
        wp1rad_lat = np.deg2rad(path[i].ycoord)
        wp1rad_lon = np.deg2rad(path[i].xcoord)
        wp2rad_lat = np.deg2rad(path[i+1].ycoord)
        wp2rad_lon = np.deg2rad(path[i+1].xcoord)
        d = 2*0.001 * rE * np.arcsin(np.sqrt((1 - np.cos(wp2rad_lat - wp1rad_lat) + np.cos(wp1rad_lat) * np.cos(
            wp2rad_lat) * (1 - np.cos(wp2rad_lon - wp1rad_lon))) / 2))
        totalDistance+=d
        i+=1
    return round(totalDistance,2)

def containsNode (P,name):
   i=0
   encontrado=False
   while i<len(P.nodes) and not encontrado:
      if name==P.nodes[i].name:
          encontrado=True
      i=i+1
   return encontrado


def getCostToNode (P,name):
   origen = P.nodes[0]
   encontrado=False
   i=0
   while i<len(P.nodes) and not encontrado:
       if name==P.nodes[i].name:
           encontrado=True
           if name==P.nodes[0].name:
               return 0
           else:
               d=distance(origen,P.nodes[i])
               return d
       i=i+1
   if encontrado==False:
       return -1


def getApproxToDest(G,P,name):
   last=P.nodes[-1]
   i=0
   encontrado=False
   while i<len(G.nodesList):
       if name==G.nodesList[i].name:
           d=distance(last,G.nodesList[i])
           encontrado=True
           return d
       i=i+1
   if encontrado==False:
       return -1

def a_star(start_name, goal_name, graph):
    start = None
    goal = None
    for node in graph.nodesList:
        if node.name == start_name:
            start = node
        elif node.name == goal_name:
            goal = node
        if start and goal:
            break

    if not (start and goal):
        return None  # One or both nodes not found

    open_set = [start]
    came_from = [None] * len(graph.nodesList)
    g_scores = [float('inf')] * len(graph.nodesList)
    g_scores[graph.nodesList.index(start)] = 0
    f_scores = [float('inf')] * len(graph.nodesList)
    f_scores[graph.nodesList.index(start)] = distance(start, goal)

    while open_set:
        current = min(open_set, key=lambda node: f_scores[graph.nodesList.index(node)])
        if current == goal:
            path = []
            while current is not None:
                path.insert(0, current)
                current = came_from[graph.nodesList.index(current)]
            return path
        open_set.remove(current)
        for neighbor in current.nList:
            tentative_g_score = g_scores[graph.nodesList.index(current)] + distance(current, neighbor)
            neighbor_index = graph.nodesList.index(neighbor)
            if tentative_g_score < g_scores[neighbor_index]:
                came_from[neighbor_index] = current
                g_scores[neighbor_index] = tentative_g_score
                f_scores[neighbor_index] = g_scores[neighbor_index] + distance(neighbor, goal)
                if neighbor not in open_set:
                    open_set.append(neighbor)
    return None


def plot_path(graph, path):
    plt.ion()

    fig, ax = plt.subplots(figsize=(16, 10))
    totalCost = 0

    # Plot nodes
    for node in graph.nodesList:
        x, y = node.xcoord, node.ycoord
        ax.scatter(x, y, color="#FF5D5D", marker="v")
        ax.text(x + 0.3, y + 0.3, node.name, fontsize=10, ha='center', va='center', color="black", weight="bold")

    # Plot the segments
    for segment in graph.segmentsList:
        x1, y1 = segment.n1.xcoord, segment.n1.ycoord
        x2, y2 = segment.n2.xcoord, segment.n2.ycoord
        ax.arrow(x1, y1, x2 - x1, y2 - y1, head_width=0.2, length_includes_head=True,
                 color="grey", width=0.07, alpha=0.25)
        ax.text((x1 + x2) / 2 + 0.2, (y1 + y2) / 2 + 0.2, round(segment.cost, 2), fontsize=10,
                ha='center', va='center')

    # Plot the path
    if path:
        for i in range(len(path) - 1):
            x1, y1 = path[i].xcoord, path[i].ycoord
            x2, y2 = path[i + 1].xcoord, path[i + 1].ycoord
            ax.plot([x1, x2], [y1, y2], color='red', linewidth=2)
            totalCost += distance(path[i], path[i + 1])

    # Set plot boundaries
    all_x = [node.xcoord for node in graph.nodesList]
    all_y = [node.ycoord for node in graph.nodesList]
    ax.set_xlim(min(all_x) - 1, max(all_x) + 1)
    ax.set_ylim(min(all_y) - 1, max(all_y) + 1)

    ax.set_title(f'Best Path (Simple Graph), Total Distance: {round(totalCost, 2)}')

    # Display the plot
    plt.show(block=True)

def plot_pathMap(graph,path,coord):
    plt.ion()

    fig, ax = plt.subplots(figsize=(16, 10))

    # Create a Basemap instance with the specified longitude and latitude range and high resolution
    m = Basemap(projection=coord[0], llcrnrlon=coord[1], llcrnrlat=coord[2], urcrnrlon=coord[3], urcrnrlat=coord[4],
                resolution=coord[5], ax=ax)

    m.drawcoastlines()
    m.drawcountries()
    m.drawmapboundary()
    m.fillcontinents(color='#009344', lake_color='#85C7D5')
    m.drawmapboundary(fill_color='#85C7D5')

    # Plot the nodes and store the text objects for adjustment
    for node in graph.nodesList:
        x, y = m(node.xcoord, node.ycoord)  # Transform coordinates
        m.plot(x, y, color="#FF5D5D", markersize=3)
        plt.text(x, y, node.name, fontsize=5, ha='center', va='center', color="black", weight="bold")

    # Plot the segments
    for segment in graph.segmentsList:
        x1, y1 = m(segment.n1.xcoord, segment.n1.ycoord)  # Transform start coordinates
        x2, y2 = m(segment.n2.xcoord, segment.n2.ycoord)  # Transform end coordinates
        plt.arrow(x1, y1, x2 - x1, y2 - y1, head_width=0.05, length_includes_head=True,
                  color="grey", width=0.001, alpha=0.25)  # Set the alpha for transparency
        plt.text((x1 + x2) / 2 + 0.005, (y1 + y2) / 2 + 0.005, round(segment.cost, 2), fontsize=5,
                 horizontalalignment='center', verticalalignment='center')

    plt.title(f'Best Path (Map), Total Distance: {totalCost(path)} Km')

    # Plot the path if provided
    if path:
        for i in range(len(path) - 1):
            x1, y1 = m(path[i].xcoord, path[i].ycoord)
            x2, y2 = m(path[i + 1].xcoord, path[i + 1].ycoord)
            plt.plot([x1, x2], [y1, y2], color='red', linewidth=2)
            plt.draw()
            plt.pause(0.5)
    plt.show(block=False)

# Example usage
# Assuming 'graph' and 'path' are defined and populated with appropriate data
# plot_path(graph, path)