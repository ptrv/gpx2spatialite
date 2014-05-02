==============
gpx2spatialite
==============
:Author: Daniel Belasco Rogers <http://planbperformance.net/dan>,
         Peter Vasil <mail@petervasil.net>

A script for importing GPX files into a SpatiaLite database.

Using Tomo Krajina's gpx module, import a file record, trackpoints and
tracklines to a database (SQL for database below)


Usage
-----

It is possible to read in single files::

  gpx2spatialite -d <path/to/database> -u <user_id> <path/to/gpx>

Or multiple folders::

  gpx2spatialite -d <path/to/database> -u <user_id> <path/to/folder1> <path/to/folder2>

Files and folders can be specified both at the same time::

  gpx2spatialite -d <path/to/database> -u <user_id> <path/to/folder1> <path/to/gpx>


Create a new database
---------------------

Run script to create a new database and initialize it::

  gpx2spatialite_create_db <path/to/new/database>


CityDefs
--------

Import/update citydefs into existing database::

  gpx2spatialite_citydefs -i <path/to/input.sql> <path/to/database>

Export citydefs table::

  gpx2spatialite_citydefs -e <path/to/output.sql> <path/to/database>


Unit tests
----------

The repository contains the standalone py.test (version 2.5.2) script
`runtests.py`.

Run the following command to run the tests::

  python setup.py test


Dependencies
------------

* gpxpy
* sqlite library with loading extension support or pyspatialite


..

   Local Variables:
   mode: rst
   End:
