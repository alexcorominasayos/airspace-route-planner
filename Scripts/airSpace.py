from navAirport import *
from navPoint import *
from path import *
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import os
class AirSpace:
    def __init__(self):
        self.navPointList=[]
        self.navSegmentList=[]
        self.navAirportList=[]

def addPoint(airSpace,navPoint):
   try:
       airSpace.navPointList.append(navPoint)
   except (ValueError):
       return -1
   except(UnboundLocalError):
       return -1


def addSegment(airSpace, numOrg, numDst, distance):
   try:
    # = navSegment(numOrg, numDst, distance) For convenience we will take the segment
    s = segment(numOrg, numDst, distance)
    airSpace.navSegmentList.append(s)

   except (ValueError):
       return -1
   except(UnboundLocalError):
       return -1


def addAirport(airSpace,name):
   try:
       airSpace.navAirportList.append(navAirport(name))
   except (ValueError):
       return -1
   except(UnboundLocalError):
       return -1

def addSID(airSpace, nameAirport, nameSID):
   try:
       i=0
       encontrado=False
       while i<len(airSpace.navAirportList) and not encontrado:
           if nameAirport==airSpace.navAirportList[i].name:
               airSpace.navAirportList[i].SIDs.append(nameSID)
               encontrado=True
           i=i+1
       if encontrado==False:
           return 0 #not in airspace
   except (ValueError):
       return -1
   except(UnboundLocalError):
       return -1


def addSTAR(airSpace,nameAirport,nameSTAR):
   try:
       i=0
       encontrado=False
       while i<len(airSpace.navAirportList) and not encontrado:
           if nameAirport==airSpace.navAirportList[i].name:
               airSpace.navAirportList[i].STARs.append(nameSTAR)
               encontrado=True
           i=i+1
       if encontrado==False:
           return 0 #not in airspace
   except (ValueError):
       return -1
   except(UnboundLocalError):
       return -1

def loadAirspace(airSpace, filename1, filename2,filename3):
    F = open(filename1, "r")
    line = F.readline().strip()
    while line != "":
        trozos = line.split(" ")
        n = navPoints(trozos[0], trozos[1], float(trozos[3]), float(trozos[2]))
        airSpace.navPointList.append(n)
        line = F.readline().strip()
    F.close()
    F = open(filename2, "r")
    line = F.readline().strip()
    while line != "":
        trozos = line.split(" ")
        for navPoint in airSpace.navPointList:
            if trozos[0] == navPoint.id:
                pointOrg=navPoint
            if trozos[1] == navPoint.id:
                pointArr=navPoint
        s=segment(pointOrg,pointArr,float(trozos[2]))
        airSpace.navSegmentList.append(s)
        line = F.readline().strip()
    F.close()
    F = open(filename3, "r")
    line = F.readline().strip()
    while line != "":
        aero = line
        i=0
        while i<len(airSpace.navPointList):
            if aero==airSpace.navPointList[i].name:
                airSpace.navAirportList.append(airSpace.navPointList[i])
            i=i+1
        line = F.readline().strip()
    F.close()

def buildAirGraph(airSpace):
    Graph1=graph([],[])
    Graph1.nodesList.extend(airSpace.navPointList)
    Graph1.segmentsList.extend(airSpace.navSegmentList)
    return Graph1


import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


def plotAirSpaceGraph(Graph, coord):
    plt.ion()  # Turn on interactive mode
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
    for node in Graph.nodesList:
        x, y = m(node.xcoord, node.ycoord)  # Transform coordinates
        m.plot(x, y, color="#FF5D5D", markersize=3, marker="v")
        ax.text(x, y, node.name, fontsize=5, ha='center', va='center', weight="bold")

    # Plot the segments
    for segment in Graph.segmentsList:
        x1, y1 = m(segment.n1.xcoord, segment.n1.ycoord)  # Transform start coordinates
        x2, y2 = m(segment.n2.xcoord, segment.n2.ycoord)  # Transform end coordinates
        plt.arrow(x1, y1, x2 - x1, y2 - y1, head_width=0.02, length_includes_head=True,
                  color="r", width=0.001, alpha=0.25)  # Set the alpha for transparency
        ax.text((x1 + x2) / 2 + 0.005, (y1 + y2) / 2 + 0.005, round(segment.cost, 2), fontsize=5,
                horizontalalignment='center', verticalalignment='center')

    if coord[1] == -1.5:
        where = "Catalonia"
    elif coord[1] == -9:
        where = "Spain"
    elif coord[1] == -5.2:
        where = "Europe"

    ax.set_title(f"Map of {where}'s Airspace")
    plt.show(block=False)
    plt.pause(0.1)  # Pause briefly to ensure the plot updates