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

Run the script::

  gpx2spatialite -d <path/to/database> -u <user_id> <path/to/gpx>


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

Run the following command to run the tests::

  python setup.py test

..

   Local Variables:
   mode: rst
   End:
