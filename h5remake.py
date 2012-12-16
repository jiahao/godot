#Combine HDF5 files
import datetime
import tables

class VehicleLocation(tables.IsDescription):
    vehicleID = tables.StringCol(4)
    route     = tables.StringCol(8)
    direction = tables.StringCol(16)
    latitude  = tables.Float64Col()   #Reported latitude
    longitude = tables.Float64Col()   #Reported longitude
    time      = tables.Float64Col()   #Time stamp in seconds since epoch time
    heading   = tables.UInt16Col()    #Heading in degrees


"Row by row copy of table - attempts to recover broken table"
if True:
    file1 = 'recover.h5'
    file2 = 'mbta_trajectories.h5'

    import os
    if os.path.exists(file1):
        print file1, 'exists. stop'
        raise 

    compressionOptions = tables.Filters(complevel=9, complib='blosc')
    f1 = tables.openFile(file1, 'w', filters = compressionOptions)
    f2 = tables.openFile(file2)

    t1 = f1.createTable('/', 'VehicleLocations', VehicleLocation,
            'MBTA vehicle positions', filters = compressionOptions)
    t2 = f2.root.VehicleLocations

    #Part 2. Parse vehicle location data.
    for n, row in enumerate(t2):
        newrow = t1.row
        print n,
        for field in ('direction', 'heading', 'latitude', 'longitude',
                'route', 'time', 'vehicleID'):
            newrow[field] = row[field]
            print field,':', row[field], ' ',
        print
        newrow.append()
        t1.flush()
    
    f1.close()
    f2.close()


