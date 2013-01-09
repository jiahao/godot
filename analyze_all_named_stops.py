#!/usr/bin/env python
import datetime 
import numpy
import tables
import time as unixtime

from scrapetimetable import *
from findspacings import *

def timestamp(thedatetime, thetime = None):
    #opposite of fromtimestamp
    if thetime is not None: #Assume it's a time object
        thisdatetime = datetime.datetime.combine(thedatetime, thetime)
    else:
        thisdatetime = thedatetime

    return unixtime.mktime(thisdatetime.timetuple())

if __name__ == '__main__':
    theroute = 1
    thedirection = 'I' #'O'
    #TODO Determine this programmatically
    direction = '1_1_var0'

    h5file = tables.openFile('mbta_trajectories.h5')

    #Extract earliest and latest time stamps for the data
    #Pytables 2.4.0 does not have min() and max() query methods...
    timestamps = h5file.root.VehicleLocations.col('time')
    earliest_date = datetime.datetime.fromtimestamp(min(timestamps)).date()
    latest_date   = datetime.datetime.fromtimestamp(max(timestamps)).date()

    bus_stop_data = ReadRouteConfig(route = theroute)

    all_data = []
    #Iterate over all timed bus stops
    for schedule_code in ['W', 'S', 'U']:
        named_bus_stops = ReadMBTATimetable(route = theroute, direction = thedirection,
                        timing = schedule_code)
        for stop_idx, stop in enumerate(named_bus_stops):
            this_bus_stop_name = stop[0].strip()
            this_bus_stop_location = getBusStopLocation(this_bus_stop_name, bus_stop_data)
            timetable_chunks = ChunkTimetable(stop[1:])
    
            print this_bus_stop_name, 'is located at', this_bus_stop_location
            
            #Now iterate over all dates 
            thedate = earliest_date
            while thedate <= latest_date:
                thenextday = thedate + datetime.timedelta(days=1)
    
                #If it's the wrong day of the week, skip
                if TimeToScheduleCode(thedate) != schedule_code:
                    thedate = thenextday #Iterate
                    continue
                
                print 'Date', thedate
                    
                #Query HDF5 data file
                starttime = timestamp(thedate, datetime.time(3, 0))
                endtime = timestamp(thenextday, datetime.time(3, 0))
    
                queryString = "((route == '%s') & (direction == '%s') & (%f <= time) & (time < %f))" % \
                        (theroute, direction, starttime, endtime) 
                trajectories = h5file.root.VehicleLocations.where(queryString)
    
                #Calculate spacings
                spacings, times = ExtractArrivalIntervals(trajectories, this_bus_stop_location,
                        doWrite = False)
        
                for idx, s in enumerate(spacings):
                    thetime = datetime.datetime.fromtimestamp(times[idx]).time()
                    #Determine which chunk it belongs to
                    chunktimes = numpy.array([c[0] for c in timetable_chunks])
                    chunk_idx = len(chunktimes[chunktimes < thetime]) - 1
                    if chunk_idx < 0:
                        chunk_idx += len(chunktimes)
                    expected_s = timetable_chunks[chunk_idx][1]
                    print stop_idx, schedule_code, chunk_idx, thetime, s, expected_s

                    all_data.append([stop_idx, schedule_code, chunk_idx, times[idx], s, expected_s])
                thedate = thenextday #Iterate

    h5file.close()

    #Save data
    import scipy
    import scipy.io as io
    data_map = {
            'stop_idxs': [x[0] for x in all_data],
            'schedule_codes': [x[1] for x in all_data],
            'chunk_idxs': [x[2] for x in all_data],
            'times'     : [x[3] for x in all_data],
            'spacings': [x[4] for x in all_data],
            'spacings_expected': [x[5] for x in all_data],
            }
    io.savemat('spacings', data_map, oned_as = 'row')
    print len(all_data), 'spacings analyzed'
