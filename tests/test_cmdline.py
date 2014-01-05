import pytest
import gpx2spatialite


@pytest.mark.usefixtures("gpx_path", "dummy_files")
class TestCmdline:

    def test_read_filepaths_and_dirs(self, gpx_path, dummy_files):
        tmp_dir = dummy_files['dir']
        tmp_file1 = dummy_files['tmp1']
        tmp_file2 = dummy_files['tmp2']

        expected = [gpx_path]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert expected == actual

        expected = [tmp_file1]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert expected == actual

        expected = [tmp_file1, tmp_file2]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert sorted(expected) == sorted(actual)

        actual = gpx2spatialite.read_filepaths([tmp_dir], ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/file*.gpx".format(tmp_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/*.gpx".format(tmp_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/*".format(tmp_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["foo".format(tmp_dir)]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert [] == actual

    def test_checkfile(self, gpx_path):
        assert gpx2spatialite.checkfile(gpx_path)
