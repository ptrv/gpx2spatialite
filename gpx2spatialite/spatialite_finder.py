# Copyright (C) 2014  Peter Vasil <mail@petervasil.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].


import sys

import sqlite3 as spatialite


def check_for_extension():
    return hasattr(spatialite.Connection, 'enable_load_extension')

LOAD_AS_EXTENSION = check_for_extension()

if not LOAD_AS_EXTENSION:
    try:
        from pysqlite2 import dbapi2 as spatialite
        LOAD_AS_EXTENSION = check_for_extension()
    except ImportError:
        LOAD_AS_EXTENSION = False

if not LOAD_AS_EXTENSION:
    try:
        from pyspatialite import dbapi2 as spatialite
    except ImportError:
        print("Please install a sqlite3 library that supports loading \
        extensions or pyspatialite")
        sys.exit(2)


def get_connection(db_path):
    connection = spatialite.connect(db_path)
    if LOAD_AS_EXTENSION:
        # print('spatialite loaded as sqlite extension')

        connection.enable_load_extension(True)

        libspatialite_shared_libs = [
            'libspatialite.so',
            'libspatialite',
            'mod_spatialite',
            '/usr/local/opt/libspatialite/lib/mod_spatialite',
            'libspatialite.dll'
        ]

        load_successfull = False
        for lib_name in libspatialite_shared_libs:
            load_ext_query = 'SELECT load_extension("{0}")'.format(lib_name)
            try:
                connection.execute(load_ext_query)
                load_successfull = True
                break
            except:
                pass

        if not load_successfull:
            print("Unable to load spatialite sqlite3 extension")
            sys.exit(0)

    return connection
