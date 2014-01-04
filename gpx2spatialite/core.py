import sys
import os.path
import hashlib
from datetime import datetime
from math import radians, atan2, sin, cos, degrees
from .spatialite_finder import spatialite, init_spatial_metadata, get_connection
from __init__ import get_data
try:
    import gpxpy
    import gpxpy.gpx
except ImportError:
    print('*' * 48)
    print('This script needs the python module gpxpy to work')
    print('')
    print('You can get it by typing:')
    print('sudo easy_install gpxpy')
    print('Or install manually from here '
          'https://pypi.python.org/pypi/gpxpy/0.8.6')
    print('*' * 48)
    sys.exit(2)
import uuid


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
    sql += "NULL, '{0}', '{1}', '{2}', '{3}', '{4}', "\
           "{5});".format(filename, md5hash, date_entered, firsttimestamp,
                          lasttimestamp, user)

    # execute insert checking whether the file has already been
    # entered
    try:
        cursor.execute(sql)
    except spatialite.IntegrityError as err:
        print("*" * 43)
        print("File already entered. Please try again")
        print(err)
        print("*" * 43)
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
            sql += "VALUES ({0}, {1}, {2}, '{3}', {4}, {5}, {6}, {7}, "\
                "GeomFromText('{8}', 4326))".format(trkseg_id,
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
            sql += "VALUES ({0}, {1}, {2}, '{3}', {4}, {5}, {6}, {7}, "\
                "{8}, GeomFromText('{9}', 4326))".format(trkseg_id,
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
        except spatialite.IntegrityError as err:
            print("Not importing duplicate point from {0}: {1}".format(time,
                                                                       err))


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
        sql += "({0}, '{1}', '{2}', {3}, {4}, {5}, {6}, {7},"\
            " GeomFromText('{8}', 4326))".format(trkseg_id,
                                                 timestamp_start,
                                                 timestamp_end,
                                                 length_m,
                                                 time_sec,
                                                 speed_kph,
                                                 file_uid,
                                                 user,
                                                 linestr)
        cursor.execute(sql)


def enterwaypoints(cursor, user, waypoints, file_uid):
    """
    """
    for wpt in waypoints:
        wpt_name, wpt_ele, wpt_time, wpt_sym, wpt_loc, wpt_geom = wpt
        if wpt_loc == -1:
            sql = "INSERT INTO waypoints (wpt_name, ele, utctimestamp, sym,"
            sql += "file_uid, user_uid, geom) VALUES "
            sql += "(\"{0}\", {1}, '{2}', \"{3}\", {4}, {5},"\
                " GeomFromText('{6}', 4326))".format(wpt_name, wpt_ele,
                                                     wpt_time, wpt_sym,
                                                     file_uid, user,
                                                     wpt_geom)
        else:
            sql = "INSERT INTO waypoints (wpt_name, ele, utctimestamp, sym,"
            sql += "file_uid, user_uid, citydef_uid, geom) VALUES "
            sql += "(\"{0}\", {1}, '{2}', \"{3}\", {4}, {5}, {6},"\
                " GeomFromText('{7}', 4326))".format(wpt_name, wpt_ele,
                                                     wpt_time, wpt_sym,
                                                     file_uid, user,
                                                     wpt_loc, wpt_geom)

        cursor.execute(sql)


def insert_segment(cursor, seg_uuid):
    """
    Insert a tracksegment into the database.

    Arguments:
    - `seg_uuid`: uuid of segment
    """
    sql = "INSERT INTO tracksegments (trkseg_uuid) VALUES"
    sql += "('{0}')".format(seg_uuid)
    cursor.execute(sql)


def get_location(cursor, lon, lat):
    """
    Query the database citydefs table to see if the point is within
    one. Return 1 (Unknown) if not
    """
    sql = "SELECT citydef_uid FROM citydefs WHERE within"
    sql += "(ST_GeomFromText('Point({0} {1})'), geom)".format(lon, lat)
    cursor.execute(sql)
    try:
        loc_id = cursor.fetchone()[0]
    except TypeError:
        # print "unknown city"
        loc_id = 1

    return loc_id


def extractpoints(filepath, cursor, skip_locs, skip_wpts):
    """
    parse the gpx file using gpxpy and return a list of lines

    line = trkseg_id, trksegpt_id, ele, time, course, speed, loc, geom

    trackpoint columns: trackpoint_uid, trkseg_id, trksegpt_id, ele,
    utctimestamp, cmt, course, speed, file_uid, user_uid, citydef_uid, geom

    trackline columns: trkline_uid, trksegid_fm_trkpts, name, cmt,
    timestamp_start, timestamp_end, length_m, time_sec, speed_kph,
    points, file_uid, user_uid, geom

    tracksegment columns: trkseg_uid, trkseg_uuid

    waypoint_line: name, ele, time, symbol, loc, geom
    """
    trklines = []
    trkpts = []
    wpts = []

    file = open(filepath)
    try:
        gpx = gpxpy.parse(file)
    except Exception as e:
        print("GPXException ({0}) for {1}: {2}.".format(type(e), filepath, e))
        return trkpts, trklines, 0, 0, wpts

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
                    geom_str = "Point({0} {1})".format(lon, lat)

                    pts_str = "{0} {1}".format(lon, lat)
                    pts_strs.append(pts_str)

                    time = point.time
                    ele = point.elevation
                    if ele is None:
                        print("No elevation recorded for "
                              "{0} - assuming 0".format(time))
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
                print("skipping segment with < 2 points")

    if not skip_wpts:
        for wpt in gpx.waypoints:
            wptline = []
            wpt_lat = wpt.latitude
            wpt_lon = wpt.longitude
            wpt_geom_str = "Point({0} {1})".format(wpt_lon, wpt_lat)

            wpt_name = wpt.name
            wpt_symbol = wpt.symbol
            wpt_time = wpt.time
            wpt_ele = wpt.elevation
            if wpt_ele is None:
                print("No elevation recorded for "
                      "{0} - assuming 0".format(wpt_time))
                wpt_ele = 0

            if not skip_locs:
                wpt_loc = get_location(cursor, wpt_lon, wpt_lat)
            else:
                wpt_loc = -1

            wptline = [wpt_name, wpt_ele, wpt_time, wpt_symbol, wpt_loc,
                       wpt_geom_str]

            wpts.append(wptline)

    return trkpts, trklines, firsttimestamp, lasttimestamp, wpts


def update_locations(connection):
    """
    Update location of points.
    """
    cur = connection.cursor()
    # cur.execute("PRAGMA foreign_keys = ON")

    sql = "select *, astext(geom) from trackpoints "
    sql += "where citydef_uid = 1 or citydef_uid is null"

    res = cur.execute(sql)
    unknowns = res.fetchall()

    print("{0} trackpoints with unknown location".format(len(unknowns)))

    num_updated = 0
    for row in unknowns:
        sql = "select * from citydefs where within("
        sql += "GeomFromText('{0}'), geom)".format(row[12])
        rs2 = cur.execute(sql)
        city = rs2.fetchone()
        if city is not None:
            sql = "update trackpoints set citydef_uid = {0} ".format(city[0])
            sql += "where trkpt_uid = {0}".format(row[0])
            cur.execute(sql)
            num_updated += 1
        elif row[10] is None:
            sql = "update trackpoints set citydef_uid = 1 "
            sql += "where trkpt_uid = {0}".format(row[0])
            cur.execute(sql)
            num_updated += 1

    print("updated {0} trackpoints".format(num_updated))

    cur.close()
    connection.commit()


def check_if_gpxfile_exists(cursor, filepath):
    """
    Checks if file is already in database.
    """
    sql = "SELECT * FROM files WHERE md5hash = '{0}'".format(getmd5(filepath))

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
    sql = "SELECT user_uid FROM users WHERE username = '{0}'".format(username)
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
    sql += "('{0}')".format(username)
    cursor.execute(sql)

    return get_user_id(cursor, username)


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
