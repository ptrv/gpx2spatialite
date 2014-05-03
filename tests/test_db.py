import pytest
import os.path
from functools import partial
import gpx2spatialite


@pytest.mark.usefixtures("gpx_path", "db")
class TestDb:
    def test_insert_user(self, db):
        cursor = db.cursor
        userid = gpx2spatialite.insert_user(cursor, "testuser2")

        assert userid == 2

        sql = "select * from users where user_uid = 2"
        res = cursor.execute(sql)
        username = res.fetchone()[1]
        assert username == "testuser2"

    def test_enterfile(self, gpx_path, db):
        cursor = db.cursor
        extracted_pts = gpx2spatialite.extractpoints(gpx_path, skip_wpts=True)

        gpx2spatialite.enterfile(gpx_path, cursor, 1,
                                 extracted_pts[2],
                                 extracted_pts[3])

        sql = "select * from files"
        res = cursor.execute(sql)
        test_file_row = res.fetchone()

        assert test_file_row[1] == os.path.basename(gpx_path)

    def get_file_and_user(self, gpx_path, db):
        cursor = db.cursor
        md5 = gpx2spatialite.getmd5(os.path.expanduser(gpx_path))

        sql = "select * from files where md5hash = '%s'" % md5
        res = cursor.execute(sql)
        file_row = res.fetchone()
        # print file_row
        return file_row[0], file_row[6]

    def test_entertrackpoints(self, gpx_path, db):
        cursor = db.cursor
        extracted_pts = gpx2spatialite.extractpoints(gpx_path)

        fileid, userid = self.get_file_and_user(gpx_path, db)
        gpx2spatialite.enterpoints(cursor, userid, extracted_pts[0],
                                   fileid, None)

        sql = "select *, astext(geom) from trackpoints"
        res = cursor.execute(sql)
        trkpt_rows = res.fetchall()

        # print trkpt_rows
        assert len(trkpt_rows) == 4

        assert trkpt_rows[1][0] == 2
        assert trkpt_rows[1][1] == -1
        assert trkpt_rows[1][2] == 1
        assert trkpt_rows[1][3] == 65.51
        assert trkpt_rows[1][4] == "2012-03-17 12:46:44"
        assert trkpt_rows[1][5] is None
        assert trkpt_rows[1][6] == -77.1362263931
        assert trkpt_rows[1][7] == 0.259243898451
        assert trkpt_rows[1][8] == 1
        assert trkpt_rows[1][9] == 1
        assert trkpt_rows[1][10] is None
        assert trkpt_rows[1][12] == "POINT(13.45717 52.511357)"

    def test_entertracklines(self, gpx_path, db):
        cursor = db.cursor
        extracted_pts = gpx2spatialite.extractpoints(gpx_path)

        fileid, userid = self.get_file_and_user(gpx_path, db)
        gpx2spatialite.enterlines(cursor, userid, extracted_pts[1],
                                  fileid, None)

        sql = "select *, astext(geom) from tracklines"
        res = cursor.execute(sql)
        trklines_rows = res.fetchall()

        assert len(trklines_rows) == 1

        assert trklines_rows[0][0] == 1
        assert trklines_rows[0][1] == -1
        assert trklines_rows[0][2] is None
        assert trklines_rows[0][3] == "2012-03-17 12:46:19"
        assert trklines_rows[0][4] == "2012-03-17 12:47:23"
        assert trklines_rows[0][5] == 56.7757773278
        assert trklines_rows[0][6] == 64.0
        assert trklines_rows[0][7] == 3.19363747469
        assert trklines_rows[0][8] == 1
        assert trklines_rows[0][9] == 1

    def test_enterwaypoints(self, gpx_path, db):
        cursor = db.cursor
        extracted_wpts = gpx2spatialite.extractpoints(gpx_path)

        fileid, userid = self.get_file_and_user(gpx_path, db)

        gpx2spatialite.enterwaypoints(cursor, userid,
                                      extracted_wpts[4], fileid)

        sql = "select *, astext(geom) from waypoints"
        res = cursor.execute(sql)
        wpt_row = res.fetchone()

        assert wpt_row[0] == 1
        assert wpt_row[1] == "001"
        assert wpt_row[2] == 195.440933
        assert wpt_row[3] == "2012-03-21 21:24:43"
        assert wpt_row[4] == "Flag, Blue"
        assert wpt_row[5] == 1
        assert wpt_row[6] == 1
        assert wpt_row[7] is None
        assert wpt_row[9] == "POINT(-121.17042 37.085751)"

    def test_check_if_table_exists(self, db):
        table_exists_func = \
            partial(gpx2spatialite.check_if_table_exists, db.conn)

        assert table_exists_func("users") is True
        assert table_exists_func("users-not-existing") is False

    def test_get_cityid_trackpoint_pairs(self, gpx_path, db):
        cursor = db.cursor
        extracted_pts = gpx2spatialite.extractpoints(gpx_path)

        fileid, userid = self.get_file_and_user(gpx_path, db)
        gpx2spatialite.enterpoints(cursor, userid, extracted_pts[0],
                                   fileid, None)

        loc_trks_func = \
            partial(gpx2spatialite.get_cityid_trackpoint_pairs, cursor)

        assert len(loc_trks_func(False)) == 4
        assert len(loc_trks_func(True)) == 0
