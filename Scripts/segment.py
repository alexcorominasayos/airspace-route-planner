from node import *

class segment:
    def __init__(self,n1,n2,cost):
        self.n1=n1
        self.n2=n2
        self.cost=cost
        n1.nList.append(n2)
#activate for normal plots
#we define object segment with 2 inputs and 3 atributes, the cost one being automatically assigned