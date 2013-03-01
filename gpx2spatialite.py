#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Started Tue 12 Feb 2013 21:48:02 CET

Using Tomo Krajina's gpx module, import a file record, trackpoints and
tracklines to a database (SQL for database below)

Copyright 2013 Daniel Belasco Rogers <http://planbperformance.net/dan>
               Peter Vasil <mail@petervasil.net>

TODO: Check what happens if a user id is entered that isn't in the database

To create a suitable database:
In spatialite-gui, click on 'Create a&New (empty)SQLite DB' (second tool
item)

To prepare the tables needed for this script (populating the users table
with 'Daniel' and 'Sophia'), run the sql file extras/create_db.sql (i.e.
open it in spatialite-gui with 'Execute SQL script'())

The script extras/drop_db.sql could be usefule too - it drops all the
tables in the database so you can start again
"""

# standard imports
import sys
import os.path
import hashlib
from datetime import datetime
from optparse import OptionParser
from math import radians, atan2, sin, cos, degrees
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
    usage = "usage: %prog [options] /path/to/gpx/file.gpx <username>"
    optparser = OptionParser(usage, version="%prog 0.2")
    optparser.add_option("-d",
                         "--database",
                         dest="dbasepath",
                         metavar="FILE",
                         default=DEFAULTDB,
                         help="Define path to alternate database")

    optparser.add_option("--updatelocations",
                         dest="update_locs",
                         default=False,
                         action="store_true",
                         help="Update locations for points \
(<username>, <gpxfile> not needed)")

    optparser.add_option("-s",
                         "--skiplocations",
                         dest="skip_locs",
                         default=False,
                         action="store_true",
                         help="Skip querying locations for points (faster)")

    (options, args) = optparser.parse_args()

    update_locations = options.update_locs

    if len(args) != 2 and update_locations is False:
        message = """
Wrong number of arguments!

Please define input GPX and username
e.g. python gpx2spatialite </path/to/gpxfile.gpx> <username>
"""
        optparser.error("\n" + message)

    dbpath = os.path.expanduser(options.dbasepath)

    if update_locations is True:
        return None, None, dbpath, None, True

    filepath = args[0]
    checkfile(filepath)

    user = args[1]
    skip_locs = options.skip_locs

    return filepath, user, dbpath, skip_locs, False


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


def getcourse(lat1, lon1, lat2, lon2):
    """
    initial course [degrees] to reach (lat2, lon2) from (lat1, lon1)
    on a great circle

    range of returned values:
    -180 < course <= 180
    (-90 = west, 0 = north, 90 = east, 180 = south)
    """
    if lat1 + 1e-10 > 90.0:
        return 180.0  # starting from north pole -> the only direction is south
    elif lat1 - 1e-10 < -90.0:
        return 0.0   # starting from south pole -> the only direction is north

    lat1rad = radians(lat1)
    lat2rad = radians(lat2)
    londiff = radians(lon2 - lon1)
    course_rad = atan2(
        sin(londiff) * cos(lat2rad),
        (cos(lat1rad) * sin(lat2rad) -
         sin(lat1rad) * cos(lat2rad) * cos(londiff)))

    return degrees(course_rad)


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


def enterpoints(cursor, user, trkpts, file_uid):
    """
    Enters points in the spatially enabled 'trackpoints' table

    trackpoint columns: trackpoint_uid, trkseg_id, trksegpt_id, ele,
    utctimestamp, name, cmt, desc, course, speed, file_uid, user_uid,
    geom

    trkpts = trkseg_id, trksegpt_id, ele, time, course, speed, loc, geom
    """
    for line in trkpts:
        trkseg_id, trksegpt_id, ele, time, course, speed, loc, geom = line
        if loc == -1:
            sql = "INSERT INTO trackpoints (trkseg_id, trksegpt_id, "
            sql += "ele, utctimestamp, course, speed, "
            sql += "file_uid, user_uid, geom) "
            sql += "VALUES (%d, %d, %f, '%s', %f, %f, %d, %d, "\
                "GeomFromText('%s', 4326))" % (trkseg_id,
                                               trksegpt_id,
                                               ele,
                                               time,
                                               course,
                                               speed,
                                               file_uid,
                                               user,
                                               geom)
        else:
            sql = "INSERT INTO trackpoints (trkseg_id, trksegpt_id, "
            sql += "ele, utctimestamp, course, speed, "
            sql += "file_uid, user_uid, citydef_uid, geom) "
            sql += "VALUES (%d, %d, %f, '%s', %f, %f, %d, %d, %d, "\
                "GeomFromText('%s', 4326))" % (trkseg_id,
                                               trksegpt_id,
                                               ele,
                                               time,
                                               course,
                                               speed,
                                               file_uid,
                                               user,
                                               loc,
                                               geom)
        try:
            cursor.execute(sql)
        except spatialite.IntegrityError as e:
            print "Not importing duplicate point from %s: %s" % (time, e)


def enterlines(cursor, user, trklines, file_uid):
    """
    trackline columns: trkline_uid, trksegid_fm_trkpts, name, cmt,
    timestamp_start, timestamp_end, length_m, time_sec, speed_kph,
    points, file_uid, user_uid, geom

    trkline = [lastseg, timestamp_start, timestamp_end,
               length_m, time_sec, speed_kph, linestr]
    """
    for line in trklines:
        (trkseg_id, timestamp_start, timestamp_end, length_m, time_sec,
         speed_kph, linestr) = line
        sql = "INSERT INTO tracklines (trkseg_id, timestamp_start, "
        sql += "timestamp_end, length_m, time_sec, speed_kph, "
        sql += "file_uid, user_uid, geom) VALUES "
        sql += "(%d, '%s', '%s', %f, %d, %f, %d, %d,"\
            " GeomFromText('%s', 4326))" % (trkseg_id,
                                            timestamp_start,
                                            timestamp_end,
                                            length_m,
                                            time_sec,
                                            speed_kph,
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
    Query the database citydefs table to see if the point is within
    one. Return 1 (Unknown) if not
    """
    sql = "SELECT citydef_uid FROM citydefs WHERE within"
    sql += "(ST_GeomFromText('Point(%f %f)'), geom)" % (lon, lat)
    cursor.execute(sql)
    try:
        loc_id = cursor.fetchone()[0]
    except TypeError:
        # print "unknown city"
        loc_id = 1

    return loc_id


def extractpoints(filepath, cursor, skip_locs):
    """
    parse the gpx file using gpxpy and return a list of lines

    line = trkseg_id, trksegpt_id, ele, time, course, speed, loc, geom

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

    firsttimestamp, lasttimestamp = gpx.get_time_bounds()

    for track in gpx.tracks:
        for segment in track.segments:
            if segment.get_points_no() > 1:
                seg_uuid = uuid.uuid4()
                insert_segment(cursor, seg_uuid)
                lastseg = getlasttrkseg(cursor)
                trksegpt_id = 0
                pts_strs = []
                lastpoint = None
                for point in segment.points:
                    lat = point.latitude
                    lon = point.longitude
                    geom_str = "Point(%f %f)" % (lon, lat)

                    pts_str = "%f %f" % (lon, lat)
                    pts_strs.append(pts_str)

                    time = point.time
                    ele = point.elevation
                    if ele is None:
                        print "No elevation recorded for "\
                            "%s - assuming 0" % time
                        ele = 0
                    speed = point.speed

                    if lastpoint:
                        lon1 = lastpoint.longitude
                        lat1 = lastpoint.latitude
                        course = getcourse(lat1, lon1, lat, lon)
                        if not speed:
                            speed = point.speed_between(lastpoint)
                            if speed is None:
                                speed = 0
                    else:
                        course = 0
                        if not speed:
                            speed = 0

                    if not skip_locs:
                        loc = get_location(cursor, lon, lat)
                    else:
                        loc = -1

                    ptline = [lastseg, trksegpt_id, ele, time,
                              course, speed, loc, geom_str]

                    trkpts.append(ptline)
                    trksegpt_id += 1
                    lastpoint = point

                timestamp_start, timestamp_end = segment.get_time_bounds()
                length_m = segment.length_2d()
                time_sec = segment.get_duration()
                try:
                    speed_kph = (length_m / time_sec) * 3.6
                except ZeroDivisionError:
                    speed_kph = 0.0
                linestr = "LINESTRING("
                linestr += ",".join(pts_strs)
                linestr += ")"
                trkline = [lastseg, timestamp_start, timestamp_end,
                           length_m, time_sec, speed_kph, linestr]
                trklines.append(trkline)
            else:
                print "skipping segment with < 2 points"

    return trkpts, trklines, firsttimestamp, lasttimestamp


def update_locations(connection):
    """
    Update location of points.
    """
    connection.cursor().execute("PRAGMA foreign_keys = ON")

    sql = "UPDATE trackpoints SET citydef_uid = 1 WHERE citydef_uid IS NULL"
    connection.cursor().execute(sql)
    connection.commit()

    sql = "UPDATE trackpoints SET citydef_uid = (SELECT citydefs.citydef_uid "
    sql += "FROM citydefs WHERE within(trackpoints.geom, citydefs.geom)) "
    sql += "WHERE (SELECT citydefs.citydef_uid FROM citydefs WHERE within"
    sql += "(trackpoints.geom, citydefs.geom)) NOT NULL"

    connection.cursor().execute(sql)
    connection.commit()


def check_if_gpxfile_exists(cursor, filepath):
    """
    Checks if file is already in database.
    """
    sql = "SELECT * FROM files WHERE md5hash = '%s'" % getmd5(filepath)

    cursor.execute(sql)

    try:
        res = cursor.fetchall()
        if len(res) > 0:
            return True
        else:
            return False
    except TypeError:
        return False


def get_user_id(cursor, username):
    """
    Gets the user id for a given username string.
    """
    sql = "SELECT user_uid FROM users WHERE username = '%s'" % (username)
    cursor.execute(sql)

    try:
        userid = cursor.fetchone()[0]
    except TypeError:
        userid = -1
    return userid


def insert_user(cursor, username):
    """
    Insert a user into the database.
    """
    sql = "INSERT INTO users ('username') VALUES"
    sql += "('%s')" % (username)
    cursor.execute(sql)

    return get_user_id(cursor, username)


def checkadd(cursor, username):
    """
    A name has been entered that is not in database. Ask if a new name
    should be added
    """
    while 1:
        question = 'Do you want to add %s as a new user? y or n ' % username
        answer = raw_input(question)
        answer = answer.lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        else:
            print "Please answer y or n"


def main():
    """
    you know what 'main' does - run everything in the right order and
    print helpful messages to stdout
    """
    # for timing (rough)
    starttime = datetime.now()

    filepath, username, dbpath, skip_locs, update_locs = parseargs()

    conn = spatialite.connect(dbpath)
    cursor = conn.cursor()

    if update_locs is True:
        update_locations(conn)
        sys.exit(0)

    userid = get_user_id(cursor, username)
    if userid == -1:
        # user name is not in database - ask to add
        if checkadd(cursor, username):
            print "User %s sucessfully added to database" % username
            userid = insert_user(cursor, username)
        else:
            print "Please run again specifying a known user:"
            sys.exit(0)

    if check_if_gpxfile_exists(cursor, filepath) is True:
        print "File already exists"
        sys.exit(2)

    print "\nParsing points in %s" % filepath
    trkpts, trklines, firsttimestamp, lasttimestamp = extractpoints(filepath,
                                                                    cursor,
                                                                    skip_locs)
    print "File first timestamp: %s, last timestamp: %s" % (firsttimestamp,
                                                            lasttimestamp)
    endtime = datetime.now()
    print "\nParsing %d points from gpx file took %s " % (len(trkpts),
                                                          endtime - starttime)
    print "Entering file into database"
    enterfile(filepath, cursor, userid, firsttimestamp, lasttimestamp)

    file_uid = getcurrentfileid(cursor)

    print "Entering points into database"
    enterpoints(cursor, userid, trkpts, file_uid)

    print "Entering lines into database"
    enterlines(cursor, userid, trklines, file_uid)

    conn.commit()
    conn.close()

    endtime = datetime.now()
    print "Script took %s\n" % (endtime - starttime)

if __name__ == '__main__':
    sys.exit(main())
