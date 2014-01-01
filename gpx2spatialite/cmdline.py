import sys
import os.path
import glob
from optparse import OptionParser

DEFAULTDB = "emptytest.sqlite"


def checkfile(filepath):
    """
    Checks if file or folder exists at location
    """
    if (os.path.isfile(filepath) or os.path.isdir(filepath)):
        return True
    else:
        return False


def parseargs():
    """
    parse command line arguments and define options etc
    """
    usage = "usage: %prog [options] <username> /path/to/gpx/file.gpx"\
            "or /path/to/folder"
    optparser = OptionParser(usage, version="%prog 0.4")
    optparser.add_option("-d",
                         "--database",
                         dest="dbasepath",
                         metavar="FILE",
                         default=DEFAULTDB,
                         help="Define path to alternate database")

    optparser.add_option("--updatelocations",
                         dest="update_locs",
                         default=False,
                         action="store_true",
                         help="Update locations for points \
(<username>, <gpxfile> not needed)")

    optparser.add_option("-s",
                         "--skiplocations",
                         dest="skip_locs",
                         default=False,
                         action="store_true",
                         help="Skip querying locations for points (faster)")

    (options, args) = optparser.parse_args()

    update_locs = options.update_locs

    if len(args) < 2 and update_locs is False:
        message = """
Wrong number of arguments!

Please define input GPX and username
e.g. python gpx2spatialite <username> </path/to/gpxfile.gpx>
"""
        optparser.error("\n" + message)

    dbpath = os.path.expanduser(options.dbasepath)

    if update_locs is True:
        return None, None, dbpath, None, True

    user = args[0]

    filepaths = args[1:]
    for f in filepaths:
        if checkfile(f) is False:
            print("{0} is not a file or directory".format(f))
            sys.exit(2)

    skip_locs = options.skip_locs

    return filepaths, user, dbpath, skip_locs, False


def checkadd(username):
    """
    A name has been entered that is not in database. Ask if a new name
    should be added
    """
    while 1:
        question = ('Do you want to add {0} as a new user? y or n '
                    .format(username))
        answer = raw_input(question)
        answer = answer.lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        else:
            print("Please answer y or n")


def read_filepaths_from_directory(rootdir, fileextension):
    """
    Returns a list of file paths recursively read starting at the given
    root directory. Files will be filtered by the given file extension.
    File names are handled case-insensitive.
    """
    if not isinstance(fileextension, str):
        raise Exception("Second parameter must be of type str.")

    paths = []
    for rootfolder, subfolders, files in os.walk(rootdir):
        filtered_files = [f for f in files if f.lower().endswith(
            fileextension)]
        for filename in filtered_files:
            filepath = glob.glob(os.path.join(rootfolder, filename))
            if isinstance(filepath, str):
                paths.append(filepath)
            if isinstance(filepath, list):
                paths += filepath
    return paths


def read_filepaths(resource_paths, fileextension):
    """
    Returns a list of file paths read from the given resource paths.
    A resource can be a file or a folder.
    Files will be filtered by the given file extension.
    File names are handled case-insensitive.
    """
    if not isinstance(resource_paths, list):
        raise Exception("First parameter must be of type list.")

    paths = []
    for resource_path in resource_paths:
        if os.path.isdir(resource_path) is True:
            filepaths = read_filepaths_from_directory(resource_path,
                                                      fileextension)
            paths.extend(filepaths)
        elif os.path.isfile(resource_path) is True:
            if resource_path.lower().endswith(fileextension):
                paths.append(resource_path)
        else:
            for fi in glob.glob(resource_path):
                if fi.lower().endswith(fileextension):
                    paths.append(fi)
    return paths