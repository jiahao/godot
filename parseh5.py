#!/usr/bin/env python
import datetime
import math
import xml.etree.ElementTree as ET
import tables

class VehicleLocation(tables.IsDescription):
    vehicleID = tables.StringCol(4)
    route     = tables.StringCol(8)
    direction = tables.StringCol(16)
    latitude  = tables.Float64Col()   #Reported latitude
    longitude = tables.Float64Col()   #Reported longitude
    time      = tables.Float64Col()   #Time stamp in seconds since epoch time
    heading   = tables.UInt16Col()    #Heading in degrees

def parse_mbta_xml(database, thefile):
    try:
        tree = ET.parse(thefile)
        root = tree.getroot()
    except ET.ParseError: #Error parsing XML content of the file
        return

    #Part 1. Get epoch time to nearest second
    #        MBTA reports in whole units of milliseconds
    report_time = long(root.find('lastTime').attrib['time'][:-3])
    
    #Part 2. Parse vehicle location data.
    for thevehicle in root.iter('vehicle'):
        rawdata = thevehicle.attrib #Raw MBTA data

        data= {}
        try:
            #Bus was here at this epoch time
            data['time']      = report_time - long(rawdata['secsSinceReport'])
            data['vehicleID'] = rawdata['id']
            data['route']     = rawdata['routeTag']
            data['direction'] = rawdata['dirTag']
            data['latitude']  = rawdata['lat']
            data['longitude'] = rawdata['lon']
            data['heading']   = rawdata['heading']
        except KeyError:
            pass
        
        #Check that this record wasn't already reported
        queryString = '((vehicleID == "%(vehicleID)s") & (time == %(time)s))' % data 
        try:
            query = database.getWhereList(queryString)
        except tables.exceptions.HDF5ExtError:
            #gets thrown whenHDF5 file is open and being written to
            print "Could not get file lock on HDF5 file. Abort."
            import sys
            sys.exit()

        if len(query) == 0:
            vehiclePosition = database.row
            for key, value in data.items():
                vehiclePosition[key] = value
            vehiclePosition.append()
        else:
            assert len(query) == 1, "OMG COLLISION"
    database.flush()



def ParseAll():
    import glob, os

    compressionOptions = tables.Filters(complevel=9, complib='blosc')
    f = tables.openFile('mbta_trajectories.h5', mode = 'a',
        filters = compressionOptions, title = 'Historical MBTA bus data')
   
    try:
        thetable = f.root.VehicleLocations
    except tables.exceptions.NoSuchNodeError:
        thetable = f.createTable('/', 'VehicleLocations', VehicleLocation,
            'MBTA vehicle positions', filters = compressionOptions)
        #Create table indexers
        thetable.cols.time.createIndex()
        thetable.cols.vehicleID.createIndex()


    for filename in sorted(glob.glob('*.xml')):
        parse_mbta_xml(thetable, filename)
        print 'Parsed', filename
        os.unlink(filename)

    f.close()

if __name__ == '__main__':
    ParseAll()

