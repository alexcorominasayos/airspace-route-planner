class Node:
    def __init__(self,name,x,y):
        self.name=str(name)
        self.xcoord=float(x)
        self.ycoord=float(y)
        self.nList=[]

#define object node

def addNeighbor (n1,n2):
    if n2 in n1.nList:
        return False
    else:
        n1.nList.append(n2)
        return True

#adds object to neighbour list

def distance(n1,n2):
   dist=(((n2.xcoord)-(n1.xcoord))**2+((n2.ycoord)-(n1.ycoord))**2)**(1/2)
   return dist

#eulerian distance formula in a float output