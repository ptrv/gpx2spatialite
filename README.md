# gpx2spatialite

A script for importing GPX files into a SpatiaLite database.

## Usage

    python ./gpx2spatialite -d <path/to/database> <path/to/gpx> <user_id>


## CityDefs

Import/update citydefs into existing database:

    spatialite <path/to/database> ".read insert_citydefs.sql utf-8"

The last command will cause errors for already existing entries and tables, but that's OK. New content will be imported anyway.

Export citydefs table:

    spatialite <path/to/database> ".dump citydefs" > insert_citydefs.sql
