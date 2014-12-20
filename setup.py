from setuptools import setup, Command

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
    with open('README.rst') as readme_file:
        return readme_file.read()

setup(description='gpx2spatialite',
      long_description=readme(),
      author='Peter Vasil, Daniel Belasco Rogers',
      url='https://github.com/ptrv/gpx2spatialite',
      download_url='https://github.com/ptrv/gpx2spatialite',
      author_email='mail@petervasil.net',
      version=__version__,
      install_requires=['gpxpy'],
      packages=['gpx2spatialite'],
      entry_points={
          'console_scripts': [
              'gpx2spatialite = gpx2spatialite.main:main'
          ]
      },
      name='gpx2spatialite',
      cmdclass={'test': PyTest},
      include_package_data=True,
      zip_safe=False,
      license='GPLv3',
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 2 :: Only',
          'Topic :: Scientific/Engineering :: GIS'
      ])
