from .core import *
from .cmdline import *
from .spatialite_finder import get_connection
from .db_helper import *

import os

__version__ = '0.5dev'

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, 'data', path)
