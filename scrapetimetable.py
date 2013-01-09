#!/usr/bin/env python
from bs4 import BeautifulSoup
from datetime import date, datetime, time, timedelta
import numpy
import urllib2
import xml.etree.ElementTree as ET

def ReadMBTATimetable(route, direction, timing):
    theURLTemplate = "http://www.mbta.com/schedules_and_maps/bus/routes/?" + \
            "route=%(route)d&direction=%(direction)s&timing=%(timing)s"
    #inbound - I
    #outbound - O
    
    #timing
    # weekday - W
    # Saturday - S
    # Sunday - U
    # todo - holidays
    
    data = {
        'route': route,
        'direction': direction,
        'timing': timing
    }
    
    theURL = theURLTemplate % data
    html_timetable = urllib2.urlopen(theURL).read()
    soup = BeautifulSoup(html_timetable)
    timetable = soup.find(id="timetable")
    if timetable is None:
        print 'No data found'
        raise
    
    timetable_data = timetable.contents
    direction = timetable_data[1].contents[0]
    named_bus_stops = [z.contents for z in timetable_data[2].contents[0].findAll('th')]
    for item in timetable_data[2].contents[1:]:
        try:
            fields = item.contents
        except AttributeError: #Not part of table
            continue
        for n, time in enumerate(fields):
            thetime = datetime.strptime(time.contents[0], u'%I:%M %p')#.time()
            named_bus_stops[n].append(thetime)
    return named_bus_stops


def ReadRouteConfig(route):
    theURLTemplate = 'http://webservices.nextbus.com/service/publicXMLFeed?command=routeConfig&a=mbta&r=%d'
    theURL = theURLTemplate % route
    html_timetable = urllib2.urlopen(theURL).read()
    root = ET.fromstring(html_timetable)
    route = root.find('route')
    assert route is not None, "Could not retrieve useable data from Nextbus.com"
    
    stops = []
    for stop in route.findall('stop'):
        stops.append(stop.attrib)

    directions = []
    for direction in route.findall('direction'):
        directions.append([direction.attrib])
        for stop in direction.findall('stop'):
            directions[-1].append(stop.attrib)
    
    #Path information - TODO use it
    #for path in route.findall('path):

    return stops, directions


def TimeToScheduleCode(thetime = None):
    if thetime is None:
        thetime = datetime.now()
    try:
        thedate = thetime.date()
    except AttributeError:
        thedate = thetime

    #Step 1: is it a holiday or other special day?
    #TODO Implement properly, list is hard-coded
    if thedate == date(2012, 12, 25): #Christmas 
        return 'U' #Sunday
    elif thedate == date(2013, 1, 1): #New Year's Day
        return 'U' #Sunday
    elif thedate == date(2013, 1, 21): #MLK Day
        return 'S' #Saturday
    elif thedate == date(2013, 2, 18): #Presidents' Day
        return 'S' #Saturday
        
    #Step 2: find out day of week
    dayofweek = thetime.weekday()

    if dayofweek == 6:   #Sunday
        return 'U'
    elif dayofweek == 5: #Saturday
        return 'S'
    else:                #Weekday
        return 'W'


def ChunkTimetable(timings):
    """
    Chunks timetable

    Input:
        Array of datetime objects representing time of day
    Output:
        Array of 3-tuples containing:
            0: start time of chunk (a datetime.time() object)
            1: mean of arrival times in chunk (min.)
            2. standard error of mean in chunk (min.)
    """

    timings = numpy.array(timings)

    spacings = numpy.diff(timings)
    #Fix negative time jump if the timetable runs past midnight
    spacings[spacings < timedelta(0)] += timedelta(hours = 24)
    #Convert to minutes
    spacings = numpy.array([s.total_seconds()/60.0 for s in spacings])
    

    #Calculate changes in spacings
    spacings2 = numpy.diff(spacings)
    idx0, doLast = 0, False
    timetable_chunks = []
    for idx, s in enumerate(spacings2):
        if idx+1 == len(spacings2):
            idx = len(spacings)
            doLast = True
        if abs(s) > 1.0 or doLast: #Ignore jumps of the nearest minute
            pop_mean = numpy.mean(spacings[idx0:idx+1])
            if idx==idx0: #Calculate standard error of mean
                pop_stderr = 0.0
            else:
                pop_stderr = numpy.std(spacings[idx0:idx+1])/numpy.sqrt(idx-idx0)

            timetable_chunks.append((timings[idx0].time(), pop_mean, pop_stderr))
            idx0 = idx+1

    return numpy.array(timetable_chunks)



def getBusStopLocation(this_bus_stop_name, bus_stop_data):
    """Search for named bus stop in bus stop data
    
    Returns:
        tuple of (latitude, longitude) for first match in bus_stop_data
        None if not found
    """
    for current_stop in bus_stop_data:
        string1 = unicode(current_stop['title'].replace('@', '&').strip())
        if string1 in this_bus_stop_name or this_bus_stop_name in string1:
            return float(current_stop['lat']), float(current_stop['lon'])
    
    #If loop ends, not found. returns None by default


if __name__ == '__main__':

    named_bus_stops = ReadMBTATimetable(route = 1, direction = 'I',
            timing = TimeToScheduleCode())
    bus_stop_data, _ = ReadRouteConfig(route = 1)

    #Match bus stop names from NextBus to MBTA website
    for stop in named_bus_stops:
        # STEP 1. Attempt to match the name of the bus stop in the timetable with
        #  a bus stop name in the Nextbus feed.
        this_bus_stop_name = stop[0].strip() #Zeroth row is a string, the rest are times
        this_bus_stop_location = getBusStopLocation(this_bus_stop_name, bus_stop_data)

        # STEP 2. Segment the timetable into times with the same expected bus spacings
        timetable_chunks = ChunkTimetable(stop[1:])

        print this_bus_stop_name, 'is located at', this_bus_stop_location
        for chunk in timetable_chunks:
            print chunk

    #print 'Bus stops:'
    #from pprint import pprint
    #pprint(named_bus_stops)

