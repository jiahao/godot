#!/usr/bin/env python
import datetime
import logging
import math
import socket
import tables
import xml.etree.ElementTree as ET

logging.basicConfig(filename = 'mbta_daemon.log', level=logging.INFO)
logger = logging.getLogger('xml2hdf5')

class VehicleLocation(tables.IsDescription):
    vehicleID = tables.StringCol(4)
    route     = tables.StringCol(8)
    direction = tables.StringCol(16)
    latitude  = tables.Float64Col()   #Reported latitude
    longitude = tables.Float64Col()   #Reported longitude
    time      = tables.Float64Col()   #Time stamp in seconds since epoch time
    heading   = tables.UInt16Col()    #Heading in degrees

def parse_mbta_xml(database, thefile, presentData = None):
    """
    Parses MBTA XML data and adds it to a HDF5 database.

    Inputs:
    database: Handle to HDF5 file
    thefile: Name of XML file to parse
    presentData: A dictionary hash of present data (to save time on the check)
                 If absent, will use database queries (much slower)
    """
    try:
        tree = ET.parse(thefile)
        root = tree.getroot()
    except ET.ParseError: #Error parsing XML content of the file
        logger.error('Could not find root of XML file: %s', thefile)
        return

    #Part 1. Get epoch time to nearest second
    #        MBTA reports in whole units of milliseconds
    timeData = root.find('lastTime')
    if timeData is None: #Maybe XML returned an error of some sort
        logger.warning('XML file %s does not have time data', thefile)
        return

    report_time = long(timeData.attrib['time'][:-3])
    
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
        
        #Part 3. Make sure record is not a duplicate
        if presentData is None:
            #No hashes. Query database to check that this record wasn't already reported
            queryString = '((vehicleID == "%(vehicleID)s") & (time == %(time)s))' % data 
            try:
                query = database.getWhereList(queryString)
            except tables.exceptions.HDF5ExtError:
                #gets thrown whenHDF5 file is open and being written to
                logger.critical("Could not get file lock on HDF5 file. Abort.")
                import sys
                sys.exit()

            if len(query) == 0:
                vehiclePosition = database.row
                for key, value in data.items():
                    vehiclePosition[key] = value
                vehiclePosition.append()
            else:
                assert len(query) == 1, "OMG COLLISION"
        else:
            #Use hashes to check if record is already reported
            if (data['vehicleID'], data['time']) not in presentData:
                vehiclePosition = database.row
                for key, value in data.items():
                    vehiclePosition[key] = value
                vehiclePosition.append()
                presentData[data['vehicleID'], data['time']] = True

    database.flush()
    logger.info('Parsed data from XML file: %s', thefile)
    return presentData


def ParseAll(theHDF5FileName = 'mbta_trajectories.h5', Cleanup = True):
    import glob, os

    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ## Create an abstract socket, by prefixing it with null. 
        s.bind('\0mbta_hdf5_writer_'+theHDF5FileName)
    
        compressionOptions = tables.Filters(complevel=9, complib='blosc')
        f = tables.openFile(theHDF5FileName, mode = 'a',
            filters = compressionOptions, title = 'Historical MBTA bus data')
   
        logging.debug('Lock acquired on %s', theHDF5FileName)
    except socket.error:
        logging.error('Lock could not be acquired on %s', theHDF5FileName)
        return

    try:
        thetable = f.root.VehicleLocations
    except tables.exceptions.NoSuchNodeError:
        thetable = f.createTable('/', 'VehicleLocations', VehicleLocation,
            'MBTA vehicle positions', filters = compressionOptions)
        #Create table indexers
        thetable.cols.time.createIndex()
        thetable.cols.vehicleID.createIndex()

    #Hash current data
    presentData = {}
    for row in thetable:
        presentData[row['vehicleID'], row['time']] = True

    for filename in sorted(glob.glob('*.xml')):
        presentData = parse_mbta_xml(thetable, filename, presentData)
        if Cleanup:
            os.unlink(filename)

    f.close()

if __name__ == '__main__':
    ParseAll()

