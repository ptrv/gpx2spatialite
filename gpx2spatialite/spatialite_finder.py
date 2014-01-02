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
        print("Please install pyspatialite")
        sys.exit(2)


def get_connection(db_path):
    connection = spatialite.connect(db_path)
    if LOAD_AS_EXTENSION:
        # print('spatialite loaded as sqlite extension')
        connection.enable_load_extension(True)
        connection.execute('SELECT load_extension("libspatialite.so")')

    return connection
