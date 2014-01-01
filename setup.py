try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


def readme():
    with open('README.rst') as readme_file:
        return readme_file.read()

setup(description='gpx2spatialite',
      long_description=readme(),
      author='Peter Vasil, Daniel Belasco Rogers',
      url='https://github.com/ptrv/gpx2spatialite',
      download_url='https://github.com/ptrv/gpx2spatialite',
      author_email='https://github.com/ptrv/gpx2spatialite',
      version='0.5',
      install_requires=['gpxpy'],
      packages=['gpx2spatialite'],
      scripts=['bin/gpx2spatialite',
               'bin/gpx2spatialite_citydefs',
               'bin/gpx2spatialite_create_db'],
      name='gpx2spatialite',
      cmdclass={'test': PyTest},
      include_package_data=True,
      zip_safe=False,
      license='GPL')
