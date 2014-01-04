from .core import *
from .cmdline import *
from .spatialite_finder import get_connection
from .db_helper import *
import os

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, 'data', path)
