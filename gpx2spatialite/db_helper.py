from spatialite_finder import get_connection
from __init__ import get_data


def create_new_db(db_path):
    connection = get_connection(db_path)
    create_db_script = get_data("sql/create_db.sql")

    cursor = connection.cursor()

    init_spatial_metadata(connection)

    create_db_query = open(create_db_script, 'r').read()
    cursor.executescript(create_db_query)
    connection.commit()

    cursor.close()
    connection.close()


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
