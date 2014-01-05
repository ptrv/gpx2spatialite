import pytest
from datetime import datetime
import gpx2spatialite


@pytest.mark.usefixtures("gpx_path", "db")
class TestGpx:
    def test_extractpoints(self, gpx_path, db):
        cursor = db.get_cursor()
        extracted_points = gpx2spatialite.extractpoints(gpx_path,
                                                        cursor,
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
