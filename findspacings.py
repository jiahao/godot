#!/usr/bin/env python
import datetime 
import numpy
import tables

def dist(origin, destination, radius = 6371.392896):
    # Haversine formula - takes spherical latitude and longitude in degrees and returns distance between the points
    # The default unit returned is in kilometers assuming the sphere has the radius of the earth
    lat1, lon1 = origin
    lat2, lon2 = destination

    dlat = numpy.radians(lat2-lat1)
    dlon = numpy.radians(lon2-lon1)
    a = numpy.sin(dlat/2) * numpy.sin(dlat/2) + numpy.cos(numpy.radians(lat1)) \
                                * numpy.cos(numpy.radians(lat2)) * numpy.sin(dlon/2) * numpy.sin(dlon/2)
    c = 2 * numpy.arctan2(numpy.sqrt(a), numpy.sqrt(1-a))
    d = radius * c
    return d


def GetAllIntervalData(VehicleLocations, route=1, direction='1_1_var0', position=(42.3589399, -71.09363)):
    #Defaults
    # 1 bus, inbound, at 84 Mass Ave

    arrivalDistanceThreshold = 0.5
    arrivalTimeThreshold = 300
    maxIntervalThreshold = 2*60*60
    queryString = "((route == '%s') & (direction == '%s'))" % (route, direction) 
    
    trajectories = VehicleLocations.where(queryString)
    queryResults = [(timePoint['time'], timePoint['vehicleID'], timePoint['latitude'], timePoint['longitude']) for timePoint in trajectories]
    queryResults = sorted(queryResults) #Sort in time
    
    # Try to determine when each bus arrived at the bus stop
    data = {}
    for timePoint in queryResults:
        theDistance = dist((timePoint[2], timePoint[3]), position)
        if theDistance > arrivalDistanceThreshold:
            #Vehicle too far away, skip
            continue
        
        theVehicle, theTime = timePoint[1], timePoint[0]
        if theVehicle in data: #If same vehicle...
            lastTime, lastDistance = data[theVehicle][-1]
            if abs(lastTime - theTime) < arrivalTimeThreshold: #and data is recent in time
                if theDistance < lastDistance:
                    #Update - bus moved closer
                    data[theVehicle].pop()
                    data[theVehicle].append((theTime, theDistance))
            else:
                data[theVehicle].append((theTime, theDistance))
        else:
            data[theVehicle] = [(theTime, theDistance)]

    #Extract arrival times
    arrivalTimesUnsorted = []
    for vehicleData in data.values():
        for times, _ in vehicleData:
            arrivalTimesUnsorted.append(times)

    arrivalTimes = (sorted(arrivalTimesUnsorted))
    #for time in arrivalTimes:
    #    print datetime.datetime.fromtimestamp(time)
    print len(arrivalTimes), "arrivals recorded"

    arrivalIntervals = numpy.diff(arrivalTimes)
    arrivalIntervals = arrivalIntervals[arrivalIntervals < maxIntervalThreshold]
    arrivalIntervals /= 60.0 #Convert to minutes
    print len(arrivalIntervals), "intervals recorded"
    #for times in sorted(arrivalIntervals):
    #    print times

    import scipy.io
    scipy.io.savemat('data.mat', {'gaps': arrivalIntervals}, oned_as='row')
    print 'data.mat saved'

def doPlot(data):
    pass

if __name__ == '__main__':
    h5file = tables.openFile('mbta_trajectories.h5')
    spacings = GetAllIntervalData(h5file.root.VehicleLocations)
    doPlot(spacings)
    h5file.close()
