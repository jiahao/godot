#Combine HDF5 files
import datetime
import tables
file1 = 'recover.h5'
file2 = 'mbta_trajectories.h5'

class VehicleLocation(tables.IsDescription):
    vehicleID = tables.StringCol(4)
    route     = tables.StringCol(8)
    direction = tables.StringCol(16)
    latitude  = tables.Float64Col()   #Reported latitude
    longitude = tables.Float64Col()   #Reported longitude
    time      = tables.Float64Col()   #Time stamp in seconds since epoch time
    heading   = tables.UInt16Col()    #Heading in degrees


if True:
    f1 = tables.openFile(file1)
    f2 = tables.openFile(file2, 'a')

    t1 = f1.root.VehicleLocations
    t2 = f2.root.VehicleLocations


    #Hash present data
    presentData = {}
    for row in t2:
        presentData[row['vehicleID'], row['time']] = True

    #Part 2. Parse vehicle location data.
    for n, row in enumerate(t1):
        #Check that this record wasn't already reported
        #queryString = '((vehicleID == "%(vehicleID)s") & (time == %(time)s))' % row
        #query = t2.getWhereList(queryString)
        if (row['vehicleID'], row['time']) not in presentData:#len(query) == 0:
            newrow = t2.row
            z = row.fetch_all_fields()
            newrow['direction'], newrow['heading'], newrow['latitude'], \
             newrow['longitude'], newrow['route'], newrow['time'], \
             newrow['vehicleID'] = z 
            newrow.append()
            t2.flush()
            print n, row['vehicleID'], datetime.datetime.fromtimestamp(row['time'])
            presentData[row['vehicleID'], row['time']] = True
        #else:
        #    assert len(query) == 1, "OMG COLLISION"
    
    f1.close()
    f2.close()


