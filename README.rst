gpx2spatialite
--------------

A script for importing GPX files into a SpatiaLite database.

Using Tomo Krajina's gpx module, import a file record, trackpoints and
tracklines to a database (SQL for database below)

Copyright 2013 Daniel Belasco Rogers <http://planbperformance.net/dan>
               Peter Vasil <mail@petervasil.net>

To create a suitable database:
In spatialite-gui, click on 'Create a New (empty) SQLite DB' (second tool
item).

To prepare the tables needed for this script (populating the users table
with a username, run the SQL file extras/create_db.sql (i.e.
open it in spatialite-gui with 'Execute SQL script'()).

The script extras/drop_db.sql could be useful too - it drops all the
tables in the database so you can start from scratch.

Usage
=====

Run the script::

  gpx2spatialite -d <path/to/database> <path/to/gpx> <user_id>


CityDefs
========

Import/update citydefs into existing database::

  gpx2spatialite_citydefs -i <path/to/database> extras/insert_citydefs.sql

Export citydefs table::

  gpx2spatialite_citydefs -e <path/to/database> extras/insert_citydefs.sql

Unit tests
==========

Run the following command to run the tests::

  python setup.py test
