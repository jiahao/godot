#!/usr/bin/env python
import datetime 
import numpy
import tables
import time as unixtime

from scrapetimetable import getBusStopLocation, ChunkTimetable, ReadRouteConfig, ReadMBTATimetable, TimeToScheduleCode
from findspacings import ExtractArrivalIntervals

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

    bus_stop_data, direction_data = ReadRouteConfig(route = theroute)

    #TODO Handle multiple variants of inbound and outbound services
    #     Right now it just matches the first variant of each
    for direction in direction_data:
        if direction[0]['name'] == 'Inbound' and thedirection == 'I':
            direction_tag = direction[0]['tag']
            stops_tags = [d['tag'] for d in direction[1:]]
            break
        elif direction[0]['name'] == 'Outbound' and thedirection == 'O':
            direction_tag = direction[0]['tag']
            stops_tags = [d['tag'] for d in direction[1:]]
            break

    assert stops_tags is not None, 'No data found for direction'

    #Match bus stoptags to GPS coordinates
    all_bus_stops = []
    for tag in stops_tags:
        match = [x for x in bus_stop_data if x['tag'] == tag][0] 
        coordinates = (float(match['lat']), float(match['lon']))
        name = match['title']
        all_bus_stops.append((coordinates, name))

    #Extract earliest and latest time stamps for the data
    #Pytables 2.4.0 does not have min() and max() query methods...
    h5file = tables.openFile('mbta_trajectories.h5')
    timestamps = h5file.root.VehicleLocations.col('time')
    earliest_date = datetime.datetime.fromtimestamp(min(timestamps)).date()
    latest_date   = datetime.datetime.fromtimestamp(max(timestamps)).date()

    all_data = []
    #Iterate over all timed bus stops
    for schedule_code in ['W', 'S', 'U']:
        named_bus_stops = ReadMBTATimetable(route = theroute, direction = thedirection,
                        timing = schedule_code)

        #Now iterate over ALL bus stops
        for stop_idx, (this_bus_stop_location, this_bus_stop_name) in enumerate(all_bus_stops):

            print 'Stop #%d:' % stop_idx, this_bus_stop_name

            #See if this is a bus stop that has a timetable on the MBTA website
            timetable_chunks = None
            for named_stop in named_bus_stops:
                named_stop_name = named_stop[0].strip()
                named_stop_location = getBusStopLocation(named_stop_name, bus_stop_data)
                if named_stop_location == this_bus_stop_location:
                    timetable_chunks = ChunkTimetable(named_stop[1:])
                    print 'Found timetable for this stop'
                    break


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
                        (theroute, direction_tag, starttime, endtime) 
                trajectories = h5file.root.VehicleLocations.where(queryString)
    
                #Calculate spacings
                spacings, times = ExtractArrivalIntervals(trajectories, this_bus_stop_location,
                        doWrite = False)
        
                for idx, s in enumerate(spacings):
                    thetime = datetime.datetime.fromtimestamp(times[idx]).time()
                    if timetable_chunks is None: #Not a bus stop with timetable data
                        chunk_idx = numpy.NaN
                        expected_s = numpy.NaN
                    else: #Have timetable data
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
