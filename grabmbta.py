#!/usr/bin/env python

"""
NextBus.com/MBTA polling daemon

This script periodically polls NextBus.com for real-time vehicle location
data from the Massachusetts Bay Transportation Authority (MBTA).

The real-time data are downloaded to time-stamped XML files.

Every hour, the daemon calls a helper code to load it all into an HDF5 database.
"""

import datetime
import gzip
import StringIO
import subprocess
import time
import urllib2

def readURL(theURL):
    """
    Reads URL, taking into account possible gzip encoding
    """
    request = urllib2.Request(theURL)
    request.add_header('Accept-encoding', 'gzip')
    try:
        response = urllib2.urlopen(request)
    except urllib2.URLError: #Network error or offline?
        return None

    if response.info().get('Content-Encoding') == 'gzip':
        responseIO = StringIO.StringIO(response.read())
        return gzip.GzipFile(fileobj=responseIO).read()
    else:
        return response.read()
    


def nextbus_daemon(polltime = 15, timeouttime = 60,
        theURL='http://webservices.nextbus.com/service/publicXMLFeed\
?command=vehicleLocations&a=mbta&t=0'):
    """
    Main daemon driver.
    
    Input
    -----
    polltime (optional): how many seconds between queries (not guaranteed to be exact)
    timeouttime (optional): how many seconds to wait after URL access error
    theURL: URL to query
    """

    lastdbaccesstime = datetime.datetime.now()
    while True:
        now = datetime.datetime.now()
        #if now.hour < 5 and now.hour > 2: #No bus service, don't bother to ask
        #    time.sleep(polltime)
        #    continue
        
        thedatetime = now.strftime('%Y-%m-%d-%H-%M-%S')
    
        #Read from URL
        thedata = readURL(theURL)
        
        if thedata is None:
            print 'Could not access Nextbus data at', thedatetime
            time.sleep(timeouttime)
            continue
    
        #Write XML file
        filename = ('mbta-' + thedatetime + '.xml')
        with open(filename, 'w') as f:
            f.write(thedata)
        
        if now - lastdbaccesstime > datetime.timedelta(hours=2):
            #Spawn new process to load up XML files into database
            print "Spawning XML reader"
            subprocess.Popen("python parseh5.py", shell=True,
                stdin=None, stdout=None, stderr=None, close_fds=True)
            lastdbaccesstime = now

        #Wait for next poll interval
        newnow = datetime.datetime.now()
        while newnow - now < datetime.timedelta(seconds = polltime):
            time.sleep(1)
            newnow = datetime.datetime.now()

if __name__ == '__main__':
    nextbus_daemon()
