class navPoints:
    def __init__(self,id,name,lat,lon):
        self.id=str(id)
        self.name=str(name)
        self.xcoord=float(lat)
        self.ycoord=float(lon)
        self.nList=[]