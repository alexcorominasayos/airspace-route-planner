from airSpace import *


def PathToKML(path, filename):
    with open(filename, "w") as F:
        F.write('<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n')
        F.write('<Document>\n')

        # Writing path as a LineString
        F.write('    <Placemark>\n')
        F.write(f'        <name>Route: {[node.name for node in path]}</name>\n')
        F.write('        <LineString>\n')
        F.write('            <altitudeMode>clampToGround</altitudeMode>\n')
        F.write('            <extrude>1</extrude>\n')
        F.write('            <tessellate>1</tessellate>\n')
        F.write('            <coordinates>\n')
        for node in path:
            F.write(f'                {node.xcoord},{node.ycoord}\n')
        F.write('            </coordinates>\n')
        F.write('        </LineString>\n')
        F.write('    </Placemark>\n')

        # Writing individual points
        for node in path:
            F.write('    <Placemark>\n')
            F.write(f'        <name>{node.name}</name>\n')
            F.write('        <Point>\n')
            F.write('            <coordinates>\n')
            F.write(f'                {node.xcoord},{node.ycoord}\n')
            F.write('            </coordinates>\n')
            F.write('        </Point>\n')
            F.write('    </Placemark>\n')

        # Writing the animated path using gx:Track
        F.write('    <Placemark>\n')
        F.write('        <name>Animated Path</name>\n')
        F.write('        <gx:Track>\n')

        for i, node in enumerate(path):
            # Set each timestamp 1 hour apart
            hour_offset = i
            timestamp = f"2024-01-01T{hour_offset:02d}:00:00Z"
            F.write(f'            <when>{timestamp}</when>\n')
            F.write(f'            <gx:coord>{node.xcoord} {node.ycoord} 0</gx:coord>\n')
        F.write('        </gx:Track>\n')
        F.write('    </Placemark>\n')

        F.write('</Document>\n')
        F.write('</kml>\n')


def PointsToKML(points, filename):
    F = open(filename, "w")
    F.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    F.write("<Document>\n")

    # Writing points
    for node in points:
        F.write(f"    <Placemark>\n")
        F.write(f"        <name>{node.name}</name>\n")
        F.write("        <Point>\n")
        F.write("            <coordinates>\n")
        F.write(f"                {node.xcoord},{node.ycoord}\n")
        F.write("            </coordinates>\n")
        F.write("        </Point>\n")
        F.write("    </Placemark>\n")

    F.write("</Document>\n")
    F.write("</kml>\n")
    F.close()


def AirSpaceRouting (airSpace, NameAirport1, NameAirport2, NameFile1,NameFile2):
    encontrado1=False
    encontrado2=False
    for node in airSpace.navAirportList:
        if NameAirport1==NameAirport2:
            return -1
        if node.name==NameAirport1:
            encontrado1=True
        if node.name==NameAirport2 and not encontrado2:
            encontrado2=True
    if encontrado1==True and encontrado2==True:
        G=buildAirGraph(airSpace)
        path = a_star(NameAirport1, NameAirport2, G)
    else:
        return -1
