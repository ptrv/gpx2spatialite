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


def init_spatial_metadata(connection):
    cursor = connection.cursor()
    result = cursor.execute('SELECT spatialite_version()')
    spatialite_version = result.fetchone()[0]

    def versionstring2list(v):
        import re
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]

    if cmp(versionstring2list(spatialite_version), [4, 1]) == -1:
        cursor.execute('SELECT InitSpatialMetaData()')
    else:
        cursor.execute('SELECT InitSpatialMetaData(1)')

    connection.commit()
