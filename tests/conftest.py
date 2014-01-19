import pytest
import os
import tempfile
from subprocess import call
from datetime import timedelta
import time
import gpx2spatialite


@pytest.fixture(scope='module')
# def set_gpx_path(request):
#     # set member variable in test class
#     request.cls.test_path = os.path.abspath("tests/data/file.gpx")
def gpx_path():
    # set member variable in test class
    return os.path.abspath("tests/data/file.gpx")


@pytest.fixture(scope='module')
def dummy_files(request):

    # dir_path = "tests/data/gpx"
    # request.cls.test_dir = os.path.abspath(dir_path)

    directory_name = tempfile.mkdtemp()

    tmp1 = tempfile.NamedTemporaryFile(suffix=".gpx",
                                       prefix="file1_",
                                       dir=directory_name)
    tmp2 = tempfile.NamedTemporaryFile(suffix=".gpx",
                                       prefix="file2_",
                                       dir=directory_name)
    tmp3 = tempfile.NamedTemporaryFile(suffix=".xml",
                                       prefix="file1_",
                                       dir=directory_name)

    # remove test dir and files
    def cleanup():
        # print('cleanup dummy files')
        tmp1.close()
        tmp2.close()
        tmp3.close()
        os.removedirs(directory_name)

    # run cleanup function after tests finished
    request.addfinalizer(cleanup)

    return {'dir': directory_name, 'tmp1': tmp1.name,
            'tmp2': tmp2.name, 'tmp3': tmp3.name}


class Db:
    def __init__(self):
        self.db_path = os.path.abspath("tests/data/db.sqlite")
        if (os.path.isfile(self.db_path)
            and time.time() - os.path.getmtime(self.db_path)
                > timedelta(days=1).total_seconds()):
            print('deleting old test database')
            call(['rm', self.db_path])

        if not os.path.isfile(self.db_path):
            gpx2spatialite.create_new_db(self.db_path)

        self.conn = gpx2spatialite.get_connection(self.db_path)
        self.cursor = self.conn.cursor()

        sql = "INSERT INTO citydefs ('city', 'country', 'geom') VALUES"
        sql += "(\"Unknown\", \"Unknown\", GeomFromText('POLYGON"
        sql += "((0 0, 0 0, 0 0, 0 0, 0 0))', 4326));"
        self.cursor.execute(sql)

        sql = "INSERT INTO citydefs ('city', 'country', 'geom') VALUES"
        sql += "(\"Berlin\", \"DE\", GeomFromText('POLYGON("
        sql += "(13.10156 52.370484, 13.10156 52.657235, 13.700291 52.657235, "
        sql += "13.700291 52.370484, 13.10156 52.370484))', 4326));"
        self.cursor.execute(sql)

        sql = "insert into users('username') values ('testuser')"
        self.cursor.execute(sql)

    # remove test database
    def cleanup(self):
        # print('cleanup database')
        self.conn.rollback()
        self.cursor.close()
        self.conn.close()
        # call(["rm", db_path])


@pytest.fixture(scope='module')
def db(request):
    db = Db()
    request.addfinalizer(db.cleanup)
    return db
