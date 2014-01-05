try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command

from gpx2spatialite import __version__


class PyTest(Command):
    description = 'Run unit tests'

    user_options = [('test-verbose', 'v', 'test verbose'),
                    ('no-capture', 's', 'disable output capturing')]

    def initialize_options(self):
        self.test_verbose = None
        self.no_capture = None

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        cmd = [sys.executable, 'runtests.py']
        if self.test_verbose:
            cmd.append('-v')
        if self.no_capture:
            cmd.append('-s')
        errno = subprocess.call(cmd)
        raise SystemExit(errno)


def readme():
    with open('README.txt') as readme_file:
        return readme_file.read()

setup(description='gpx2spatialite',
      long_description=readme(),
      author='Peter Vasil, Daniel Belasco Rogers',
      url='https://github.com/ptrv/gpx2spatialite',
      download_url='https://github.com/ptrv/gpx2spatialite',
      author_email='https://github.com/ptrv/gpx2spatialite',
      version=__version__,
      install_requires=['gpxpy'],
      packages=['gpx2spatialite'],
      scripts=['bin/gpx2spatialite',
               'bin/gpx2spatialite_citydefs',
               'bin/gpx2spatialite_create_db'],
      name='gpx2spatialite',
      cmdclass={'test': PyTest},
      include_package_data=True,
      zip_safe=False,
      license='LICENSE.txt')
