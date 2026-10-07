import matplotlib.pyplot as plt
import numpy as np
from segment import *

class graph:
    def __init__(self,nodesList,segmentsList):
        self.nodesList=nodesList
        self.segmentsList=segmentsList

#we define object graph

def addNode(g,node):
    if node in g.nodesList:
        return False
    else:
        g.nodesList.append(node)
        return True

#we add node to the node list

def addSegment(g,name1,name2):
    try:
        for node in g.nodesList:
            if node.name==name1:
                n1=node
            if node.name==name2:
                n2=node
        if (n2 or n1) in g.nodesList:
            s=segment(n1,n2)
            g.segmentsList.append(s)
            return True
    except(UnboundLocalError):
        return False

#we add a segment to the segment list correcting for error in case of not finding said value

def plot(g):
    plt.ion()
    plt.clf()
    plt.grid(color="green",linestyle="--",linewidth=.5)
    for node in g.nodesList:
        plt.text(node.xcoord+0.3,node.ycoord+0.3,str(node.name),fontsize=10\
        ,horizontalalignment='center',verticalalignment='center')
        plt.scatter(node.xcoord, node.ycoord, color="black")
        plt.draw()
        plt.pause(0.05)
    for segment in g.segmentsList:
        x1=segment.n1.xcoord
        x2=segment.n2.xcoord
        y1 = segment.n1.ycoord
        y2 = segment.n2.ycoord
        plt.arrow(x1,y1,x2-x1,y2-y1,head_width=.3,length_includes_head=True,color="r")
        plt.text((x1+x2)/2+.3,(y1+y2)/2+.3,round(segment.cost,2),fontsize=9\
        ,horizontalalignment='center',verticalalignment='center')
        plt.draw()
        plt.pause(0.05)
    plt.show(block=False)

#we plot iterating through all segments and nodes

def plotNode(g,n):
    try:
        plt.ion()
        plt.clf()
        plt.grid(color="green", linestyle="--", linewidth=.5)
        for node in g.nodesList:
            plt.scatter(node.xcoord, node.ycoord, color="gray")
            plt.text(node.xcoord + 0.3, node.ycoord + 0.3, str(node.name), fontsize=10\
                   , horizontalalignment='center', verticalalignment='center')
            plt.draw()
            plt.pause(0.05)
            if node.name == n:
                nodeMain = node
        i=0
        while i<(len(nodeMain.nList)):
            x1 = nodeMain.xcoord
            x2 = nodeMain.nList[i].xcoord
            y1 = nodeMain.ycoord
            y2 = nodeMain.nList[i].ycoord
            plt.arrow(x1, y1, x2 - x1, y2 - y1, head_width=.3, length_includes_head=True, color="r")
            plt.text((x1 + x2) / 2 + .3, (y1 + y2) / 2 + .3, round(((x2-x1)**2+(y2-y1)**2)**(1/2), 2), fontsize=9 \
                  , horizontalalignment='center', verticalalignment='center')
            plt.draw()
            plt.pause(0.05)
            i+=1
        plt.show(block=True)
    except(UnboundLocalError):
        return False

#we plot iterating only through the selected node atributes