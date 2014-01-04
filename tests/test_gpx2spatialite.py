import gpx2spatialite
import os.path
import tempfile
from subprocess import call
from datetime import datetime, timedelta
import time
try:
    import pytest
except ImportError:
    print(48 * "*")
    print("Please install 'pytest' module")
    print('')
    print('You can get it by typing:')
    print('sudo easy_install pytest')
    print('Or install manually from here '
          'https://pypi.python.org/pypi/pytest/2.3.4')
    print(48 * "*")


@pytest.fixture(scope="class")
def set_gpx_path(request):
    # set member variable in test class
    request.cls.test_path = os.path.abspath("tests/data/file.gpx")


@pytest.fixture(scope="class")
def setup_dummy_files(request):

    # dir_path = "tests/data/gpx"
    # request.cls.test_dir = os.path.abspath(dir_path)

    directory_name = tempfile.mkdtemp()
    request.cls.test_dir = directory_name

    tmp1 = tempfile.NamedTemporaryFile(suffix=".gpx",
                                       prefix="file1_",
                                       dir=directory_name)
    tmp2 = tempfile.NamedTemporaryFile(suffix=".gpx",
                                       prefix="file2_",
                                       dir=directory_name)
    tmp3 = tempfile.NamedTemporaryFile(suffix=".xml",
                                       prefix="file1_",
                                       dir=directory_name)

    request.cls.tmp_file1 = tmp1.name
    request.cls.tmp_file2 = tmp2.name
    request.cls.tmp_file3 = tmp3.name

    # remove test dir and files
    def cleanup():
        tmp1.close()
        tmp2.close()
        tmp3.close()
        os.removedirs(directory_name)

    # run cleanup function after tests finished
    request.addfinalizer(cleanup)


@pytest.fixture(scope="class")
def setup_db(request):
    db_path = os.path.abspath("tests/data/db.sqlite")
    if (os.path.isfile(db_path)
        and time.time() - os.path.getmtime(db_path) >
            timedelta(days=1).total_seconds()):
        print('deleting old test database')
        call(['rm', db_path])

    if not os.path.isfile(db_path):
        gpx2spatialite.create_new_db(db_path)

    conn = gpx2spatialite.get_connection(db_path)
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
@pytest.mark.usefixtures("setup_dummy_files")
class TestGpx2Spatialite:

    def test_read_filepaths_and_dirs(self):
        expected = [self.test_path]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert expected == actual

        expected = [self.tmp_file1]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert expected == actual

        expected = [self.tmp_file1, self.tmp_file2]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert sorted(expected) == sorted(actual)

        actual = gpx2spatialite.read_filepaths([self.test_dir], ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/file*.gpx".format(self.test_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/*.gpx".format(self.test_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/*".format(self.test_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["foo".format(self.test_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert [] == actual

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
        assert trkpt_rows[1][6] == -77.1362263931
        assert trkpt_rows[1][7] == 0.259243898451
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
        assert trklines_rows[0][5] == 56.7757773278
        assert trklines_rows[0][6] == 64.0
        assert trklines_rows[0][7] == 3.19363747469
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
        assert wpt_row[2] == 195.440933
        assert wpt_row[3] == "2012-03-21 21:24:43"
        assert wpt_row[4] == "Flag, Blue"
        assert wpt_row[5] == 1
        assert wpt_row[6] == 1
        assert wpt_row[7] is None
        assert wpt_row[9] == "POINT(-121.17042 37.085751)"
