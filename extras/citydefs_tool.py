#/usr/bin/env python
#-*- coding:utf-8 -*-

import os.path
import sys
import re
from optparse import OptionParser
from pyspatialite import dbapi2 as spatialite


def parseargs():
    """
    Parse commandline arguments
    """
    usage = "usage: %prog /path/to/database.sqlite /path/to/input_output.sql"
    optparser = OptionParser(usage, version="%prog 0.1")
    optparser.add_option("-e",
                         "--export",
                         dest="export_citydefs",
                         default=False,
                         action="store_true",
                         help="Export citydefs")
    optparser.add_option("-i",
                         "--import",
                         dest="import_citydefs",
                         default=False,
                         action="store_true",
                         help="Import citydefs")

    (options, args) = optparser.parse_args()
    if len(args) != 2:
        error = "Specify a database path and an import/export sql file"
        optparser.error(error)
        sys.exit(2)
    dbpath = os.path.expanduser(args[0])
    in_out_file = args[1]
    is_export = options.export_citydefs
    is_import = options.import_citydefs

    return is_export, is_import, dbpath, in_out_file


def export_citydefs(cursor, out_file):
    """
    Export citydefs from database to a sql insert script.
    """
    sql = "SELECT citydef_uid, city, country, AsText(geom) "
    sql += "FROM citydefs ORDER BY citydef_uid"
    cursor.execute(sql)

    out_file.write("BEGIN TRANSACTION;\n")
    for row in cursor.fetchall():
        line = "INSERT INTO citydefs ('city', 'country', 'geom') VALUES"
        line += "(\"%s\", \"%s\", "
        line += "GeomFromText('%s', 4326));\n" % (row[1].encode('utf-8'),
                                                  row[2].encode('utf-8'),
                                                  row[3].encode('utf-8'))
        out_file.write(line)
    out_file.write("COMMIT;\n")


def import_citydefs(cursor, sql_file):
    """
    Import citydefs from a sql insert script.
    """
    sql_lines = sql_file.readlines()
    for line in sql_lines:
        if re.match("BEGIN TRANSACTION|COMMIT", line) is None:
            try:
                cursor.execute(line)
            except spatialite.IntegrityError:
                pass


def main():

    is_export, is_import, dbpath, filepath = parseargs()

    conn = spatialite.connect(dbpath)
    cursor = conn.cursor()

    if is_export:
        with open(filepath, "w",) as f:
            export_citydefs(cursor, f)
    elif is_import:
        with open(filepath, "r") as f:
            import_citydefs(cursor, f)
            conn.commit()
    else:
        sys.exit(2)

    conn.close()


if __name__ == '__main__':
    sys.exit(main())
