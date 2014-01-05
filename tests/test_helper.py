import pytest
import os.path
import gpx2spatialite


@pytest.mark.usefixtures("gpx_path")
class TestHelper:
    def test_getmd5(self, gpx_path):
        file_path = os.path.expanduser(gpx_path)
        md5 = gpx2spatialite.getmd5(file_path)

        assert md5 == "17228581bc70c73205e3031041ab1656"

    def test_get_course(self):
        lat1 = 52.5113534275
        lon1 = 13.4571944922
        lat2 = 52.5113568641
        lon2 = 13.4571697656

        course_expected = -77.1362263930987
        course_actual = gpx2spatialite.get_course(lat1, lon1, lat2, lon2)
        assert course_actual == course_expected
