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
from .helper import get_course


def extractpoints(filepath, last_segment_num=-1, get_loc_func=None,
                  skip_wpts=False):
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
    segs = []

    try:
        with open(filepath) as gpx_file:
            try:
                gpx = gpxpy.parse(gpx_file)
            except Exception as e:
                print("GPXException ({0}) for {1}: {2}.".format(type(e),
                                                                filepath,
                                                                e))
                return trkpts, trklines, 0, 0, wpts, segs

            firsttimestamp, lasttimestamp = gpx.get_time_bounds()

            lastseg = last_segment_num

            for track in gpx.tracks:
                for segment in track.segments:
                    if segment.get_points_no() > 1:
                        seg_uuid = uuid.uuid4()
                        lastseg += 1
                        segs.append([lastseg, seg_uuid])
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
                                course = get_course(lat1, lon1, lat, lon)
                                if not speed:
                                    speed = point.speed_between(lastpoint)
                                    if speed is None:
                                        speed = 0
                            else:
                                course = 0
                                if not speed:
                                    speed = 0

                            if get_loc_func:
                                loc = get_loc_func(lon, lat)
                            else:
                                loc = -1

                            ptline = [lastseg, trksegpt_id, ele, time,
                                      course, speed, loc, geom_str]

                            trkpts.append(ptline)
                            trksegpt_id += 1
                            lastpoint = point

                        timestamp_start, timestamp_end \
                            = segment.get_time_bounds()
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

                    if get_loc_func:
                        wpt_loc = get_loc_func(wpt_lon, wpt_lat)
                    else:
                        wpt_loc = -1

                    wptline = [wpt_name, wpt_ele, wpt_time, wpt_symbol,
                               wpt_loc, wpt_geom_str]

                    wpts.append(wptline)

            return trkpts, trklines, firsttimestamp, lasttimestamp, wpts, segs

    except IOError as err:
        print(err)
        sys.exit(2)
