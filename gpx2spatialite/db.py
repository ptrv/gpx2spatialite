# Copyright (C) 2013, 2014
# Daniel Belasco Rogers <http://planbperformance.net/dan>,
# Peter Vasil <mail@petervasil.net>
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
import os.path
import re
from datetime import datetime
from functools import partial
from . import spatialite_finder
from . import helper


def enterfile(filepath, cursor, user, firsttimestamp, lasttimestamp):
    """
    Enters the file in the files database table for future tracking
    """
    # define fields required for file insert
    filename = os.path.split(filepath)[1]
    md5hash = helper.getmd5(filepath)
    date_entered = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # build sql
    sql = ("INSERT INTO files (file_uid, filename, "
           "md5hash, date_entered, first_timestamp, last_timestamp, user_uid) "
           "VALUES (NULL, '{0}', '{1}', '{2}', '{3}', '{4}', {5});")

    sql = sql.format(filename, md5hash, date_entered, firsttimestamp,
                     lasttimestamp, user)

    # execute insert checking whether the file has already been
    # entered
    try:
        cursor.execute(sql)
    except spatialite_finder.spatialite.IntegrityError as err:
        print("*" * 43)
        print("File already entered. Please try again")
        print(err)
        print("*" * 43)
        sys.exit(2)

    return


def get_currentfileid(cursor):
    """
    query the database for the id number of the file just entered
    """
    sql = "SELECT seq FROM sqlite_sequence WHERE name = 'files'"
    cursor.execute(sql)
    file_uid = cursor.fetchone()[0]

    return file_uid


def get_lasttrkseg(cursor):
    """
    query the database for the last trkseg_id
    """
    sql = ("SELECT trkseg_uid FROM tracksegments "
           "ORDER BY trkseg_uid DESC LIMIT 1")
    cursor.execute(sql)
    try:
        lasttrkseg = cursor.fetchone()[0]
    except TypeError:
        # there are no tracks in the database
        lasttrkseg = -1
    return lasttrkseg


def insert_segments(cursor, segment_uuids):
    """
    Insert segment uuids and return a dictionary with uuid and table uid
    association
    """
    segments_dict = {}
    for seg_uuid in segment_uuids:
        insert_segment(cursor, seg_uuid)
        segments_dict[seg_uuid] = get_lasttrkseg(cursor)

    return segments_dict


def enterpoints(cursor, user, trkpts, file_uid, segments_dict):
    """
    Enters points in the spatially enabled 'trackpoints' table

    trackpoint columns: trackpoint_uid, trkseg_id, trksegpt_id, ele,
    utctimestamp, name, cmt, desc, course, speed, file_uid, user_uid,
    geom

    trkpts = trkseg_id, trksegpt_id, ele, time, course, speed, loc, geom
    """
    for line in trkpts:
        trkseg_uuid, trksegpt_id, ele, time, course, speed, loc, geom = line

        trkseg_uid = -1
        if segments_dict is not None:
            try:
                trkseg_uid = segments_dict[trkseg_uuid]
            except KeyError:
                pass

        if loc == -1:
            sql = ("INSERT INTO trackpoints (trkseg_id, trksegpt_id, "
                   "ele, utctimestamp, course, speed, file_uid, user_uid, "
                   "geom) VALUES ({0}, {1}, {2}, '{3}', {4}, {5}, {6}, {7}, "
                   "GeomFromText('{8}', 4326))")

            sql = sql.format(trkseg_uid, trksegpt_id, ele, time, course,
                             speed, file_uid, user, geom)

        else:

            sql = ("INSERT INTO trackpoints (trkseg_id, trksegpt_id, "
                   "ele, utctimestamp, course, speed, file_uid, user_uid, "
                   "citydef_uid, geom)VALUES ({0}, {1}, {2}, '{3}', {4}, {5}, "
                   "{6}, {7}, {8}, GeomFromText('{9}', 4326))")

            sql = sql.format(trkseg_uid, trksegpt_id, ele, time, course,
                             speed, file_uid, user, loc, geom)

        try:
            cursor.execute(sql)
        except spatialite_finder.spatialite.IntegrityError as err:
            msg = "Not importing duplicate point from {0}: {1}"
            print(msg.format(time, err))


def enterlines(cursor, user, trklines, file_uid, segments_dict):
    """
    trackline columns: trkline_uid, trksegid_fm_trkpts, name, cmt,
    timestamp_start, timestamp_end, length_m, time_sec, speed_kph,
    points, file_uid, user_uid, geom

    trkline = [lastseg, timestamp_start, timestamp_end,
               length_m, time_sec, speed_kph, linestr]
    """
    for line in trklines:
        (trkseg_uuid, timestamp_start, timestamp_end, length_m, time_sec,
         speed_kph, linestr) = line

        trkseg_uid = -1
        if segments_dict is not None:
            try:
                trkseg_uid = segments_dict[trkseg_uuid]
            except KeyError:
                pass

        sql = ("INSERT INTO tracklines (trkseg_id, timestamp_start, "
               "timestamp_end, length_m, time_sec, speed_kph, file_uid, "
               "user_uid, geom) VALUES({0}, '{1}', '{2}', {3}, {4}, {5}, "
               "{6}, {7}, GeomFromText('{8}', 4326))")

        sql = sql.format(trkseg_uid, timestamp_start, timestamp_end, length_m,
                         time_sec, speed_kph, file_uid, user, linestr)

        cursor.execute(sql)


def enterwaypoints(cursor, user, waypoints, file_uid):
    """
    """
    for wpt in waypoints:
        wpt_name, wpt_ele, wpt_time, wpt_sym, wpt_loc, wpt_geom = wpt
        if wpt_loc == -1:
            sql = ("INSERT INTO waypoints (wpt_name, ele, utctimestamp, sym,"
                   "file_uid, user_uid, geom) VALUES(\"{0}\", {1}, '{2}',"
                   " \"{3}\", {4}, {5}, GeomFromText('{6}', 4326))")

            sql = sql.format(wpt_name, wpt_ele, wpt_time, wpt_sym, file_uid,
                             user, wpt_geom)

        else:

            sql = ("INSERT INTO waypoints (wpt_name, ele, utctimestamp, sym,"
                   "file_uid, user_uid, citydef_uid, geom) VALUES "
                   "(\"{0}\", {1}, '{2}', \"{3}\", {4}, {5}, {6},"
                   " GeomFromText('{7}', 4326))")

            sql = sql.format(wpt_name, wpt_ele, wpt_time, wpt_sym, file_uid,
                             user, wpt_loc, wpt_geom)

        cursor.execute(sql)


def insert_segment(cursor, seg_uuid):
    """
    Insert a tracksegment into the database.

    Arguments:
    - `seg_uuid`: uuid of segment
    """
    sql = ("INSERT INTO tracksegments (trkseg_uuid) VALUES"
           "('{0}')").format(seg_uuid)
    cursor.execute(sql)


def get_location(cursor, lon, lat):
    """
    Query the database citydefs table to see if the point is within
    one. Return 1 (Unknown) if not
    """
    sql = ("SELECT citydef_uid FROM citydefs WHERE within"
           "(ST_GeomFromText('Point({0} {1})'), geom)").format(lon, lat)
    cursor.execute(sql)
    try:
        loc_id = cursor.fetchone()[0]
    except TypeError:
        # print "unknown city"
        loc_id = 1

    return loc_id


def check_if_gpxfile_exists(cursor, filepath):
    """
    Checks if file is already in database.
    """
    sql = "SELECT * FROM files WHERE md5hash = '{0}'".format(
        helper.getmd5(filepath))

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
    sql = "INSERT INTO users ('username') VALUES" "('{0}')".format(username)
    cursor.execute(sql)

    return get_user_id(cursor, username)


def get_location_func(cursor):
    """Return the partial function for the location lookup"""
    return partial(get_location, cursor)


def update_locations(cursor, locations_list):
    """
    update the table with the list from getlocations
    """
    num_updated = 0
    for loc in locations_list:
        sql = ("UPDATE trackpoints SET citydef_uid = {0} "
               "WHERE trkpt_uid = {1}").format(loc[0], loc[1])
        cursor.execute(sql)
        num_updated += 1

    return num_updated


def reset_cities(cursor):
    """
    reset all cities to 1 (unknown)
    """
    sql = "UPDATE trackpoints SET citydef_uid = 1"
    cursor.execute(sql)


def get_cityid_trackpoint_pairs(cursor, unknown_only):
    """
    Get a list of trackpoint ids and the location id of that
    trackpoint from the citydefs table
    """

    sql = ("SELECT citydefs.citydef_uid, trackpoints.trkpt_uid "
           "FROM citydefs, trackpoints "
           "WHERE within(trackpoints.geom, citydefs.geom)")

    if unknown_only is True:
        sql += " AND trackpoints.citydef_uid = 1"

    results = cursor.execute(sql)
    locations_list = results.fetchall()

    return locations_list


def export_citydefs(cursor, out_file):
    """
    Export citydefs from database to a sql insert script.
    """
    sql = "SELECT citydef_uid, city, country, AsText(geom) "
    sql += "FROM citydefs ORDER BY country, city"
    cursor.execute(sql)

    out_file.write("BEGIN TRANSACTION;\n")
    rows = cursor.fetchall()
    for row in rows:
        line = "INSERT INTO citydefs ('city', 'country', 'geom') VALUES"
        line += "(\"%s\", \"%s\", "\
                "GeomFromText('%s', 4326));\n" % (row[1].encode('utf-8'),
                                                  row[2].encode('utf-8'),
                                                  row[3].encode('utf-8'))
        out_file.write(line)
    out_file.write("COMMIT;\n")

    return len(rows)


def import_citydefs(cursor, sql_file):
    """
    Import citydefs from a sql insert script.
    """
    sql_str = sql_file.read()
    sql_stmts = sql_str.split(';')

    num_inserted = 0
    num_failed = 0
    for stmt in sql_stmts:
        if re.search(r"INSERT INTO", stmt):
            try:
                cursor.execute(stmt + ';')
                num_inserted += 1
            except spatialite_finder.spatialite.IntegrityError:
                num_failed += 1

    return num_inserted, num_failed
