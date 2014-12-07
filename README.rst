==============
gpx2spatialite
==============
:Author: Daniel Belasco Rogers <dan@planbperformance.net>,
         Peter Vasil <mail@petervasil.net>

.. image:: https://travis-ci.org/ptrv/gpx2spatialite.svg?branch=master
   :target: https://travis-ci.org/ptrv/gpx2spatialite

.. image:: https://pypip.in/version/gpx2spatialite/badge.svg
   :target: https://pypi.python.org/pypi/gpx2spatialite/
   :alt: Latest Version

.. image:: https://pypip.in/py_versions/gpx2spatialite/badge.svg
   :target: https://pypi.python.org/pypi/gpx2spatialite/
   :alt: Supported Python versions

.. image:: https://pypip.in/license/gpx2spatialite/badge.svg
   :target: https://pypi.python.org/pypi/gpx2spatialite/
   :alt: License

|

A script for importing GPX files into a SpatiaLite database.

Uses Tomo Krajina's gpx module. gpx2spatialite takes a single or
folder full of gpx files and imports them into a spatialite spatial
database. On importing, a file is hashed and entered into a table
to make sure that a file with identical contents is not added
twice. The spatial information from trackpoints is stored in two
tables in the spatialite database, trackpoints and tracklines which
are related. You can read more detail about the reason to represent
data from a GPX file like this here:
<http://planbperformance.net/dan/blog/?p=984>

The compulsory 'user' argument is to import gpx files from
different users into the same database. This is because
gpx2spatialite was written as an importer for DrawingLife
<https://github.com/ptrv/drawinglife> which is a visualisation
software written by Peter Vasil for Daniel Belasco Rogers' and
Sophia New's art project of recording everywhere they go with a GPS
since 2003 and 2007 respectively (<http://belasconew.com/works/lifedrawing/>)

If you only have one user to enter, just pick any name and import
all files under this name.

Because DrawingLife has text at the top of the screen which shows
the current location of the animation screen, this information is
provided by the citydef_uid column in the trackpoints table which
points to the citydefs table. This column is also populated on
import by default. If you do not require this, you can set the
option -s --skip-locations which will speed up importing
considerably.

Installation
------------

gpx2spatialite is available via pip. To install it with user scope run the following command::

  pip install gpx2spatialite --user

Make sure that ``$HOME/.local/bin`` is available in your ``PATH`` environment variable.
Otherwise the gpx2spatialite executable will not be found when you run it from the shell::

  PATH=$PATH:$HOME/.local/bin


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

Each trackpoint has a location assigned to it which is used for the
`drawinglife <https://github.com/ptrv/drawinglife>`_ animation.

These are defined at import time unless the option `-s` or
`--skip-locations` is passed.

Locations are defined in the `citydefs` table in the database,
created and populated automatically by 'gpx2spatialite_create_db'.

Import citydefs into existing database::

  gpx2spatialite_citydefs -i <path/to/input.sql> <path/to/database>

Export citydefs table::

  gpx2spatialite_citydefs -e <path/to/output.sql> <path/to/database>

After adding new locations to the citydefs table, you can look for
currently unknown trackpoints and assign them to any relevant,
newly defined locations with::

  gpx2spatialite_updatelocs <path/to/database>

If you have redefined currently assigned locations or completely
changed the citydefs table, you will want to redefine every
trackpoint in the database, for which you use the `-a` or
`-all-locations` option to the above script::

  gpx2spatialite_updatelocs -a <path/to/database>


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
