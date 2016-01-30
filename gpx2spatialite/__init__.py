import os

__version__ = '0.8.2'

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, 'data', path)

__all__ = ['gpx', 'db', 'cmdline', 'helper', 'spatialite_finder', 'db_helper',
           'gpx2spatialite']
