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


from . import spatialite_finder
from . import get_data


def create_new_db(db_path):
    connection = spatialite_finder.get_connection(db_path)
    create_db_script = get_data("sql/create_db.sql")

    init_spatial_metadata(connection)

    try:
        with open(create_db_script, 'r') as f:
            create_db_query = f.read()
            try:
                with connection:
                    connection.executescript(create_db_query)
            except spatialite_finder.spatialite.Error as err:
                print('SQL Error: ' + str(err))
    except IOError as err:
        print(err)

    connection.close()


def init_spatial_metadata(connection):
    result = connection.execute('SELECT spatialite_version()')
    spatialite_version = result.fetchone()[0]

    from distutils.version import LooseVersion
    if LooseVersion(spatialite_version) < LooseVersion('4.1'):
        query = 'SELECT InitSpatialMetaData()'
    else:
        query = 'SELECT InitSpatialMetaData(1)'

    try:
        with connection:
            connection.execute(query)
    except spatialite_finder.spatialite.Error as err:
        print('SQL Error: ' + str(err))


def check_if_table_exists(connection, table_name):
    """
    Returns True if table exists otherwise False
    """
    if connection is None:
        raise "Invalid connection"

    if table_name is None or len(table_name) < 1:
        raise "Invalid table name"

    sql = "SELECT count(*) FROM sqlite_master "
    sql += "WHERE name='{0}' and type='table'"
    cursor = connection.execute(sql.format(table_name))
    return True if int(cursor.fetchone()[0]) > 0 else False
