==============
gpx2spatialite
==============
:Author: Daniel Belasco Rogers <http://planbperformance.net/dan>,
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

A script for importing GPX files into a SpatiaLite database.

Using Tomo Krajina's gpx module, import a file record, trackpoints and
tracklines to a database (SQL for database below)

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
