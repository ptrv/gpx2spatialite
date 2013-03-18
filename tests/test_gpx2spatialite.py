import gpx2spatialite
import os.path
from subprocess import call
from datetime import datetime
try:
    import pytest
except ImportError:
    print 48 * "*"
    print "Please install 'pytest' module"
    print
    print 'You can get it by typing:'
    print 'sudo easy_install pytest'
    print 'Or install manually from here '\
        'https://pypi.python.org/pypi/pytest/2.3.4'
    print 48 * "*"
from pyspatialite import dbapi2 as spatialite


@pytest.fixture(scope="class")
def set_gpx_path(request):
    # set member variable in test class
    request.cls.test_path = os.path.abspath("tests/data/file.gpx")


@pytest.fixture(scope="class")
def setup_db(request):
    db_path = os.path.abspath("tests/data/db.sqlite")
    if not os.path.isfile(db_path):
        create_db_script = os.path.abspath("extras/create_db.sql")
        spatialite_cmd_str = ".read %s utf-8" % create_db_script
        create_cmd = ["spatialite", db_path, spatialite_cmd_str]

        # create database
        call(create_cmd)

    conn = spatialite.connect(db_path)
    cursor = conn.cursor()

    # cursor.execute("savepoint test")
    # conn.commit()
    # set member variables in test class to access them later
    # request.cls is calling class
    request.cls.conn = conn
    request.cls.cursor = cursor
    request.cls.dbpath = db_path

    sql = "INSERT INTO citydefs ('city', 'country', 'geom') VALUES"
    sql += "(\"Unknown\", \"Unknown\", GeomFromText('POLYGON"
    sql += "((0 0, 0 0, 0 0, 0 0, 0 0))', 4326));"
    cursor.execute(sql)

    sql = "INSERT INTO citydefs ('city', 'country', 'geom') VALUES"
    sql += "(\"Berlin\", \"DE\", GeomFromText('POLYGON("
    sql += "(13.10156 52.370484, 13.10156 52.657235, 13.700291 52.657235, "
    sql += "13.700291 52.370484, 13.10156 52.370484))', 4326));"
    cursor.execute(sql)

    sql = "insert into users('username') values ('testuser')"
    cursor.execute(sql)

    # conn.commit()

    # remove test database
    def cleanup():
        conn.rollback()
        cursor.close()
        conn.close()
        # call(["rm", db_path])

    # run cleanup function after tests finished
    request.addfinalizer(cleanup)


@pytest.mark.usefixtures("set_gpx_path")
@pytest.mark.usefixtures("setup_db")
class TestGpx2Spatialite:

    def test_checkfile(self):
        assert gpx2spatialite.checkfile(self.test_path)

    def test_getmd5(self):
        file_path = os.path.expanduser(self.test_path)
        md5 = gpx2spatialite.getmd5(file_path)

        assert md5 == "17228581bc70c73205e3031041ab1656"

    def test_getcourse(self):
        lat1 = 52.5113534275
        lon1 = 13.4571944922
        lat2 = 52.5113568641
        lon2 = 13.4571697656

        course_expected = -77.1362263930987
        course_actual = gpx2spatialite.getcourse(lat1, lon1, lat2, lon2)
        assert course_actual == course_expected

    def test_extractpoints(self):
        extracted_points = gpx2spatialite.extractpoints(self.test_path,
                                                        self.cursor,
                                                        True, False)
        assert len(extracted_points) == 5

        expected_starttime = datetime.strptime('2012-03-17T12:46:19Z',
                                               '%Y-%m-%dT%H:%M:%SZ')
        expected_endtime = datetime.strptime('2012-03-17T12:47:23Z',
                                             '%Y-%m-%dT%H:%M:%SZ')
        assert expected_starttime == extracted_points[2]
        assert expected_endtime == extracted_points[3]

        assert len(extracted_points[0]) == 4
        assert len(extracted_points[1]) == 1

        assert len(extracted_points[4]) == 2

    def test_insert_user(self):
        userid = gpx2spatialite.insert_user(self.cursor, "testuser2")

        assert userid == 2

        sql = "select * from users where user_uid = 2"
        res = self.cursor.execute(sql)
        username = res.fetchone()[1]
        assert username == "testuser2"

    def test_enterfile(self):
        extracted_points = gpx2spatialite.extractpoints(self.test_path,
                                                        self.cursor,
                                                        True, True)

        gpx2spatialite.enterfile(self.test_path, self.cursor, 1,
                                 extracted_points[2],
                                 extracted_points[3])

        sql = "select * from files"
        res = self.cursor.execute(sql)
        test_file_row = res.fetchone()

        assert test_file_row[1] == os.path.basename(self.test_path)

    def get_file_and_user(self):
        md5 = gpx2spatialite.getmd5(os.path.expanduser(self.test_path))

        sql = "select * from files where md5hash = '%s'" % md5
        res = self.cursor.execute(sql)
        file_row = res.fetchone()

        return file_row[0], file_row[6]

    def test_entertrackpoints(self):
        extracted_pts = gpx2spatialite.extractpoints(self.test_path,
                                                     self.cursor,
                                                     True, False)

        fileid, userid = self.get_file_and_user()
        gpx2spatialite.enterpoints(self.cursor, userid,
                                   extracted_pts[0], fileid)

        sql = "select *, astext(geom) from trackpoints"
        res = self.cursor.execute(sql)
        trkpt_rows = res.fetchall()

        assert len(trkpt_rows) == 4

        assert trkpt_rows[1][0] == 2
        assert trkpt_rows[1][1] == 3
        assert trkpt_rows[1][2] == 1
        assert trkpt_rows[1][3] == 65.51
        assert trkpt_rows[1][4] == "2012-03-17 12:46:44"
        assert trkpt_rows[1][5] is None
        assert trkpt_rows[1][6] == -77.136226
        assert trkpt_rows[1][7] == 0.259244
        assert trkpt_rows[1][8] == 1
        assert trkpt_rows[1][9] == 1
        assert trkpt_rows[1][10] is None
        assert trkpt_rows[1][12] == "POINT(13.45717 52.511357)"

    def test_entertracklines(self):
        extracted_pts = gpx2spatialite.extractpoints(self.test_path,
                                                     self.cursor,
                                                     True, False)

        fileid, userid = self.get_file_and_user()
        gpx2spatialite.enterlines(self.cursor, userid,
                                  extracted_pts[1], fileid)

        sql = "select *, astext(geom) from tracklines"
        res = self.cursor.execute(sql)
        trklines_rows = res.fetchall()

        assert len(trklines_rows) == 1

        assert trklines_rows[0][0] == 1
        assert trklines_rows[0][1] == 4
        assert trklines_rows[0][2] is None
        assert trklines_rows[0][3] == "2012-03-17 12:46:19"
        assert trklines_rows[0][4] == "2012-03-17 12:47:23"
        assert trklines_rows[0][5] == 56.775777
        assert trklines_rows[0][6] == 64.0
        assert trklines_rows[0][7] == 3.193637
        assert trklines_rows[0][8] == 1
        assert trklines_rows[0][9] == 1

    def test_enterwaypoints(self):
        extracted_wpts = gpx2spatialite.extractpoints(self.test_path,
                                                      self.cursor,
                                                      True, False)

        fileid, userid = self.get_file_and_user()

        gpx2spatialite.enterwaypoints(self.cursor, userid,
                                      extracted_wpts[4], fileid)

        sql = "select *, astext(geom) from waypoints"
        res = self.cursor.execute(sql)
        wpt_row = res.fetchone()

        assert wpt_row[0] == 1
        assert wpt_row[1] == "001"
        assert wpt_row[2] == 195.0
        assert wpt_row[3] == "2012-03-21 21:24:43"
        assert wpt_row[4] == "Flag, Blue"
        assert wpt_row[5] == 1
        assert wpt_row[6] == 1
        assert wpt_row[7] is None
        assert wpt_row[9] == "POINT(-121.17042 37.085751)"
