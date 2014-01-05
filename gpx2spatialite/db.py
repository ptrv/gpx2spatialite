# Copyright (C) 2013, 2014  Daniel Belasco Rogers <http://planbperformance.net/dan>,
#                           Peter Vasil <mail@petervasil.net>
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
from datetime import datetime
from .spatialite_finder import spatialite
from .helper import getmd5


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


def get_currentfileid(cursor):
    """
    query the database for the id number of the file just entered
    """
    sql = "SELECT seq FROM sqlite_sequence "
    sql += "WHERE name = 'files'"
    cursor.execute(sql)
    file_uid = cursor.fetchone()[0]

    return file_uid


def get_lasttrkseg(cursor):
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
