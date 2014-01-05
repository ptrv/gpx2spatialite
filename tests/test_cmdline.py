import pytest
import gpx2spatialite


@pytest.mark.usefixtures("gpx_path", "dummy_files")
class TestCmdline:

    def test_read_filepaths_and_dirs(self, gpx_path, dummy_files):
        expected = [gpx_path]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert expected == actual

        expected = [dummy_files[1]]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert expected == actual

        expected = [dummy_files[1], dummy_files[2]]
        actual = gpx2spatialite.read_filepaths(expected, ".gpx")
        assert sorted(expected) == sorted(actual)

        actual = gpx2spatialite.read_filepaths([dummy_files[0]], ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/file*.gpx".format(dummy_files[0])]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/*.gpx".format(dummy_files[0])]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["{0}/*".format(dummy_files[0])]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert sorted(expected) == sorted(actual)

        input_path = ["foo".format(dummy_files[0])]
        actual = gpx2spatialite.read_filepaths(input_path, ".gpx")
        assert [] == actual

    def test_checkfile(self, gpx_path):
        assert gpx2spatialite.checkfile(gpx_path)
