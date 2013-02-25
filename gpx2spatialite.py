#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Started Tue 12 Feb 2013 21:48:02 CET

Using the osgeo ogr GPX driver, import a file record, trackpoints and
tracklines to a database (SQL for database below)

Copyright 2013 Daniel Belasco Rogers <http://planbperformance.net/dan>
               Peter Vasil <mail@petervasil.net>

To create a suitable database:
In spatialite-gui, click on 'Create a&New (empty)SQLite DB' (second tool item)

To prepare the tables needed for this script (populating the users
table with 'Daniel' and 'Sophia'), run the following sql (save as an
sql file and open it in spatialite-gui with 'Execute SQL script'())

-- Creates tables for homebrew gps repository.
-- Tables:
-- users
-- files
-- trackpoints
-- tracklines

PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

CREATE TABLE users (
user_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL,
UNIQUE (username));

INSERT INTO 'users' VALUES (1,'Daniel');
INSERT INTO 'users' VALUES (2,'Sophia');

CREATE TABLE files (
file_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
filename TEXT NOT NULL,
md5hash TEXT NOT NULL,
date_entered TEXT NOT NULL,
first_timestamp TEXT NOT NULL,
last_timestamp TEXT NOT NULL,
user_uid INTEGER UNSIGNED NOT NULL,
FOREIGN KEY (user_uid)
REFERENCES users (user_uid),
UNIQUE (md5hash));

CREATE TABLE trackpoints (
trkpt_uid INTEGER PRIMARY KEY AUTOINCREMENT,
--track_id INTEGER,
trkseg_id INTEGER,
trksegpt_id INTEGER,
ele DOUBLE NOT NULL,
utctimestamp TEXT NOT NULL,
--name TEXT,
cmt TEXT,
--desc TEXT,
course DOUBLE,
speed DOUBLE,
file_uid INTEGER UNSIGNED NOT NULL,
user_uid INTEGER UNSIGNED NOT NULL,
citydef_uid INTEGER UNSIGNED NOT NULL,
FOREIGN KEY (file_uid)
REFERENCES file (file_uid),
FOREIGN KEY (user_uid)
REFERENCES users (user_uid),
FOREIGN KEY (trkseg_id)
REFERENCES tracksegments (trkseg_uid),
FOREIGN KEY (citydef_uid)
REFERENCES citydefs (citydef_uid),
UNIQUE (utctimestamp, user_uid));

SELECT AddGeometryColumn('trackpoints', 'geom', 4326, 'POINT', 'XY');

-- CREATE TRIGGER "ggi_trackpoints_geom" BEFORE INSERT ON "trackpoints"
-- FOR EACH ROW BEGIN
-- SELECT RAISE(ROLLBACK, '"trackpoints"."geom" violates Geometry constraint [geom-type or SRID not allowed]')
-- WHERE (SELECT type FROM geometry_columns
-- WHERE f_table_name = 'trackpoints' AND f_geometry_column = 'geom'
-- AND GeometryConstraints(NEW."geom", type, srid, 'XY') = 1) IS NULL;
-- END;

CREATE TABLE tracklines (
trkline_uid INTEGER PRIMARY KEY AUTOINCREMENT,
trkseg_id INTEGER,
name TEXT,
--cmt TEXT,
--desc TEXT,
timestamp_start TEXT NOT NULL,
timestamp_end TEXT NOT NULL,
--link TEXT,
--type TEXT,
length_m DOUBLE,
time_sec DOUBLE,
speed_kph DOUBLE,
--points INTEGER,
file_uid INTEGER UNSIGNED NOT NULL,
user_uid INTEGER UNSIGNED NOT NULL,
FOREIGN KEY (file_uid)
REFERENCES file (file_uid),
FOREIGN KEY (user_uid)
REFERENCES users (user_uid),
FOREIGN KEY (trkseg_id)
REFERENCES tracksegments (trkseg_uid),
UNIQUE (timestamp_start, user_uid, trkseg_id)
);

SELECT AddGeometryColumn('tracklines', 'geom', 4326, 'LINESTRING', 'XY');

-- CREATE TRIGGER "ggi_tracklines_geom" BEFORE INSERT ON "tracklines"
-- FOR EACH ROW BEGIN
-- SELECT RAISE(ROLLBACK, '"tracklines"."geom" violates Geometry constraint [geom-type or SRID not allowed]')
-- WHERE (SELECT type FROM geometry_columns
-- WHERE f_table_name = 'tracklines' AND f_geometry_column = 'geom'
-- AND GeometryConstraints(NEW."geom", type, srid, 'XY') = 1) IS NULL;
-- END;

CREATE TABLE citydefs (
citydef_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
city TEXT NOT NULL,
country TEXT NOT NULL,
UNIQUE(city, country)
);

SELECT AddGeometryColumn('citydefs', 'geom', 4326, 'POLYGON', 'XY');

CREATE TABLE tracksegments (
trkseg_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
trkseg_uuid TEXT NOT NULL,
UNIQUE(trkseg_uuid)
);

COMMIT;

This SQL might also be useful - it drops all the tables in the
database so you can start again

BEGIN TRANSACTION;
DROP TABLE tracklines;
DROP TABLE trackpoints;
DROP TABLE tracksegments;
DROP TABLE files;
DROP TABLE users;
DROP TABLE citydefs;
COMMIT;

"""

# standard imports
import sys
import os.path
import hashlib
from datetime import datetime
from optparse import OptionParser
# these might need installing
from pyspatialite import dbapi2 as spatialite
try:
    import gpxpy
    import gpxpy.gpx
except ImportError:
    print '*' * 48
    print 'This script needs the python module gpxpy to work'
    print
    print 'You can get it by typing:'
    print 'sudo easy_install gpxpy'
    print 'Or install manually from here '\
        'https://pypi.python.org/pypi/gpxpy/0.8.6'
    print '*' * 48
    sys.exit(2)
import uuid

DEFAULTDB = "~/dansdocs/databases/emptytest.sqlite"


def checkfile(filepath):
    """
    Checks if file exists at location
    TODO check if it's a GPX file - How?
    """
    if not(os.path.isfile(filepath)):
        print '*' * 48
        print "%s is not a file" % filepath
        print "please retry with a file path e.g."\
            " ~/currentGPS/dan2012/1_originalfiles/2012-D-01.gpx"
        print '*' * 48
        sys.exit(2)
    return


def parseargs():
    """
    parse command line arguments and define options etc
    """
    usage = "usage: %prog /path/to/gpx/file.gpx"
    optparser = OptionParser(usage, version="%prog 0.1")
    optparser.add_option("-d",
                         "--database",
                         dest="dbasepath",
                         metavar="FILE",
                         default=DEFAULTDB,
                         help="Define path to alternate database")
    (options, args) = optparser.parse_args()
    if len(args) != 2:
        message = """
Please define input GPX file and user number
1=Daniel 2=Sophia
e.g. python gpx2spatialite ~/path/to/gpxfile.gpx 1"""
        # optparser.error("\nplease define input GPX file and user")
        optparser.error("\n" + message)
    filepath, user = args
    checkfile(filepath)
    dbpath = os.path.expanduser(options.dbasepath)
    return filepath, user, dbpath


def getmd5(filepath):
    """
    generates md5 hexdigests from files (necessary for the file table)

    Source:
    http://stackoverflow.com/a/11143944/464831
    """
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def enterfile(filepath, cursor, user, firsttimestamp, lasttimestamp):
    """
    Enters the file in the files database table for future tracking
    """
    # define fields required for file insert
    filename = os.path.split(filepath)[1]
    md5hash = getmd5(filepath)
    date_entered = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # build sql
    sql = "INSERT INTO files (file_uid, filename, "
    sql += "md5hash, date_entered, first_timestamp, last_timestamp, user_uid) "
    sql += "VALUES ("
    sql += "NULL, '%s', '%s', '%s', '%s', '%s', %d);" % (filename,
                                                         md5hash,
                                                         date_entered,
                                                         firsttimestamp,
                                                         lasttimestamp,
                                                         user)

    # execute insert checking whether the file has already been
    # entered
    try:
        cursor.execute(sql)
    except spatialite.IntegrityError as e:
        print "*" * 43
        print "File already entered. Please try again"
        print e
        print "*" * 43
        sys.exit(2)

    return


def getcurrentfileid(cursor):
    """
    query the database for the id number of the file just entered
    """
    sql = "SELECT seq FROM sqlite_sequence "
    sql += "WHERE name = 'files'"
    cursor.execute(sql)
    file_uid = cursor.fetchone()[0]

    return file_uid


def getlasttrkseg(cursor):
    """
    query the database for the last trkseg_id
    """
    sql = "SELECT trkseg_uid FROM tracksegments "
    sql += "ORDER BY trkseg_uid DESC LIMIT 1"
    cursor.execute(sql)
    try:
        lasttrkseg = cursor.fetchone()[0]
    except TypeError:
        # there are no tracks in the database
        lasttrkseg = -1
    return lasttrkseg


def timetodatetime(timestring):
    """
    """
    outputdatetime = datetime.strptime(timestring, '%Y/%m/%d %H:%M:%S+00')
    return outputdatetime


def enterpoints(cursor, user, trkpts, file_uid):
    """
    Enters points in the spatially enabled 'trackpoints' table
    trackpoint columns: trackpoint_uid, trkseg_id, trksegpt_id, ele,
    utctimestamp, name, cmt, desc, course, speed, file_uid, user_uid,
    geom

    trkpts = trkseg_id, trksegpt_id, ele, time, lat, lon
    """

    # iterate through lines, forming an sql and updating as we
    # go. Execute many wasn't possible because of forming strings for
    # geometry instead of triggering function

    for line in trkpts:
        trkseg_id, trksegpt_id, ele, time, loc, geom = line
        sql = "INSERT INTO trackpoints (trkseg_id, trksegpt_id, "
        sql += "ele, utctimestamp, file_uid, user_uid, citydef_uid, geom) "
        sql += "VALUES (%d, %d, %f, '%s', %d, %d, %d,"\
            "GeomFromText('%s', 4326))" % (trkseg_id,
                                           trksegpt_id,
                                           ele,
                                           time,
                                           file_uid,
                                           user,
                                           loc,
                                           geom)
        cursor.execute(sql)


def enterlines(cursor, user, trklines, file_uid):
    """
    trkline = [trkseg_id, timestamp_start, timestamp_end, linestr]
    """
    for line in trklines:
        trkseg_id, timestamp_start, timestamp_end, linestr = line
        sql = "INSERT INTO tracklines (trkseg_id, timestamp_start, "
        sql += "timestamp_end, file_uid, user_uid, geom) VALUES "
        sql += "(%d, '%s', '%s', %d, %d, "\
            "GeomFromText('%s', 4326))" % (trkseg_id,
                                           timestamp_start,
                                           timestamp_end,
                                           file_uid,
                                           user,
                                           linestr)
        cursor.execute(sql)


def insert_segment(cursor, seg_uuid):
    """
    Insert a tracksegment into the database.

    Arguments:
    - `seg_uuid`: uuid of segment
    """
    sql = "INSERT INTO tracksegments (trkseg_uuid) VALUES"
    sql += "('%s')" % (seg_uuid)
    cursor.execute(sql)


def get_location(cursor, lon, lat):
    """
    """
    sql = "SELECT citydef_uid FROM citydefs WHERE within"
    sql += "(ST_GeomFromText('Point(%f %f)'), geom)" % (lon, lat)
    cursor.execute(sql)
    try:
        loc_id = cursor.fetchone()[0]
    except TypeError:
        # unknown city
        loc_id = 1

    return loc_id


def extractpoints(filepath, cursor):
    """
    parse the gpx file using gpxpy and return a list of lines

    line = trkseg_id, trksegpt_id, ele, time, loc, geom

    trackpoint columns: trackpoint_uid, trkseg_id, trksegpt_id, ele,
    utctimestamp, cmt, course, speed, file_uid, user_uid, citydef_uid, geom

    trackline columns: trkline_uid, trksegid_fm_trkpts, name, cmt,
    timestamp_start, timestamp_end, length_m, time_sec, speed_kph,
    points, file_uid, user_uid, geom

    tracksegment columns: trkseg_uid, trkseg_uuid
    """
    trklines = []
    trkpts = []

    gpx = gpxpy.parse(open(filepath))

    for track in gpx.tracks:
        for segment in track.segments:
            if segment.get_points_no() > 1:
                seg_uuid = uuid.uuid4()
                insert_segment(cursor, seg_uuid)
                lastseg = getlasttrkseg(cursor)
                trksegpt_id = 0
                pts_strs = []
                for point in segment.points:
                    geom_str = "Point(%f %f)" % (point.longitude,
                                                 point.latitude)

                    pts_str = "%f %f" % (point.longitude, point.latitude)
                    pts_strs.append(pts_str)

                    time = point.time
                    ele = point.elevation

                    loc = get_location(cursor, point.longitude, point.latitude)

                    ptline = [lastseg, trksegpt_id, ele, time, loc, geom_str]
                    trkpts.append(ptline)
                    trksegpt_id += 1

                pt_start = segment.points[0]
                pt_end = segment.points[segment.get_points_no() - 1]
                timestamp_start = pt_start.time
                timestamp_end = pt_end.time
                linestr = "LINESTRING("
                linestr += ",".join(pts_strs)
                linestr += ")"
                trkline = [lastseg, timestamp_start, timestamp_end, linestr]
                trklines.append(trkline)
            else:
                print "skipping segment with < 2 points"

    return trkpts, trklines


def main():
    """
    you know what 'main' does - run everything in the right order and
    print helpful messages to stdout
    """
    # for timing (rough)
    starttime = datetime.now()

    # get file path
    filepath, user, dbpath = parseargs()
    user = int(user)

    # connect to the database and make a cursor
    conn = spatialite.connect(dbpath)
    cursor = conn.cursor()

    trkpts, trklines = extractpoints(filepath, cursor)

    endtime = datetime.now()
    print "\nParsing %d points from gpx file took %s " % (len(trkpts),
                                                          endtime - starttime)

    # enter the file in the file table
    print "Entering file into database"
    firsttimestamp = trkpts[0][3]
    lasttimestamp = trkpts[len(trkpts) - 1][3]
    print "File first timestamp: %s, last timestamp: %s" % (firsttimestamp,
                                                            lasttimestamp)
    enterfile(filepath, cursor, user, firsttimestamp, lasttimestamp)

    # get just entered file id from file just entered
    file_uid = getcurrentfileid(cursor)

    # enter the trackpoints from the gpx file into the trackpoint
    # table (get lasttrkseg and file_uid from this function to pass on
    # to the enterlines function)
    print "Entering points into database"
    enterpoints(cursor, user, trkpts, file_uid)

    # enter the lines into the database - either query the points in
    # the database just entered, or cycle through the list of tupes
    # (lines)
    print "Entering lines into database"
    enterlines(cursor, user, trklines, file_uid)

    # commit changes to database and close connection
    conn.commit()
    conn.close()

    endtime = datetime.now()
    print "Script took %s\n" % (endtime - starttime)

if __name__ == '__main__':
    sys.exit(main())
