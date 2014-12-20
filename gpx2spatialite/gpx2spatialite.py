#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Copyright (C) 2013, 2014
# Daniel Belasco Rogers <http://planbperformance.net/dan>,
# Peter Vasil <mail@petervasil.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

import sys
import os.path
import argparse
from datetime import datetime
from . import spatialite_finder
from . import db
from . import db_helper
from . import gpx
from . import cmdline
from . import get_data, __version__


def create_db(args_dict):

    new_db = args_dict['new_dbpath']
    custom_citydefs = args_dict['custom_citydefs']
    no_citydefs = args_dict['no_citydefs']
    exec_script = args_dict['execute_script']

    db_helper.create_new_db(new_db)

    conn = spatialite_finder.get_connection(new_db)

    def print_file_not_exists(file_name):
        print("'{0}' does not exist".format(file_name))

    if no_citydefs is False:
        if custom_citydefs is None:
            insert_citydefs_script = get_data("sql/insert_citydefs.sql")
        else:
            insert_citydefs_script = custom_citydefs

        try:
            with open(insert_citydefs_script, 'r') as f:
                insert_citydefs_query = f.read()
                try:
                    with conn:
                        conn.executescript(insert_citydefs_query)
                except spatialite_finder.spatialite.Error as err:
                    print("SQL Error: " + str(err))
        except IOError:
            print_file_not_exists(insert_citydefs_script)

    if exec_script is not None:
        try:
            with open(exec_script, 'r') as f:
                custom_script = f.read()
                try:
                    with conn:
                        conn.executescript(custom_script)
                except spatialite_finder.spatialite.Error as err:
                    print("SQL Error: " + str(err))
        except IOError:
            print_file_not_exists(exec_script)

    conn.close()


def citydefs(args_dict):

    dbpath = os.path.expanduser(args_dict['dbpath'])
    import_file = args_dict['import_citydefs']
    export_file = args_dict['export_citydefs']
    quiet = args_dict['quiet']

    cmdline.set_print_verbose(not quiet)

    conn = spatialite_finder.get_connection(dbpath)
    cursor = conn.cursor()

    if export_file:
        with open(export_file, "w",) as f:
            num_exported = db.export_citydefs(cursor, f)
            cmdline.print_cmdline(
                'Exported {0} locations'.format(num_exported))
    elif import_file:
        try:
            with open(import_file, "r") as f:
                num_i, num_f = db.import_citydefs(cursor, f)
                conn.commit()
                cmdline.print_cmdline('Imported {0} locations'.format(num_i))
                if num_f > 0:
                    cmdline.print_cmdline('{0} locations failed'.format(num_f))
        except IOError as err:
            print(err)

    cursor.close()
    conn.close()


def update_locs(args_dict):
    """
    """
    dbpath = os.path.expanduser(args_dict['dbpath'])
    all_locs = args_dict['all_locs']
    quiet = args_dict['quiet']

    cmdline.set_print_verbose(not quiet)

    # -------------------------------------------------------------------------
    starttime = datetime.now()
    # -------------------------------------------------------------------------
    conn = spatialite_finder.get_connection(dbpath)
    cursor = conn.cursor()

    # -------------------------------------------------------------------------

    cmdline.print_cmdline("*" * 48)

    if all_locs is True:

        cmdline.print_cmdline(
            "Resetting all trackpoints to location 1 (unknown)")
        db.reset_cities(cursor)

        cmdline.print_cmdline(
            "Generating a list of trackpoints and cities to update")

    else:

        cmdline.print_cmdline(
            "Generating a list with trackpoints with unknown cities to update")

    locations_list = db.get_cityid_trackpoint_pairs(cursor, not all_locs)

    cmdline.print_cmdline(
        "Updating {0} trackpoints".format(len(locations_list)))
    db.update_locations(cursor, locations_list)

    # -------------------------------------------------------------------------

    cursor.close()
    conn.commit()
    conn.close()

    # -------------------------------------------------------------------------

    endtime = datetime.now()
    cmdline.print_cmdline("Script took {0}".format(endtime - starttime))
    cmdline.print_cmdline("*" * 48)


def importer(args_dict):
    """
    you know what 'main' does - run everything in the right order and
    print helpful messages to stdout
    """

    # -------------------------------------------------------------------------

    filepaths_tmp = args_dict['gpx_files']
    filepaths = []
    for f in filepaths_tmp:
        if cmdline.checkfile(f):
            filepaths.append(f)
        else:
            cmdline.print_cmdline("{0} is not a file or directory".format(f))
    username = args_dict['user']
    dbpath = os.path.expanduser(args_dict['dbpath'])
    skip_locs = args_dict['skip_locs']
    quiet = args_dict['quiet']

    # -------------------------------------------------------------------------

    # for timing (rough)
    starttime = datetime.now()

    cmdline.set_print_verbose(not quiet)

    conn = spatialite_finder.get_connection(dbpath)
    cursor = conn.cursor()

    # -------------------------------------------------------------------------

    gpx_filepaths = cmdline.read_filepaths(filepaths, ".gpx")
    cmdline.print_cmdline(
        "\nFound {0} .gpx files.\n".format(len(gpx_filepaths)))

    if len(gpx_filepaths) == 0:
        print("No input files!")
        sys.exit(1)

    # -------------------------------------------------------------------------

    if not db_helper.check_if_table_exists(conn, "users"):
        msg = ("Unable to find database table \"users\".\n Use "
               "`gpx2spatialite create_db` to create the database beforehand.")
        print(msg)
        cursor.close()
        conn.close()
        sys.exit(1)

    userid = db.get_user_id(cursor, username)
    if userid == -1:
        # user name is not in database - ask to add
        if cmdline.checkadd(username):
            msg = "User {0} sucessfully added to database".format(username)
            cmdline.print_cmdline(msg)
            userid = db.insert_user(cursor, username)
            conn.commit()
        else:
            print("Please run again specifying a known user:")
            cursor.close()
            conn.close()
            sys.exit(1)

    # -------------------------------------------------------------------------

    get_loc_func = None if skip_locs else db.get_location_func(cursor)

    # -------------------------------------------------------------------------

    for filepath in gpx_filepaths:

        # ---------------------------------------------------------------------

        if db.check_if_gpxfile_exists(cursor, filepath) is True:
            cmdline.print_cmdline(
                "File {0} already in database".format(filepath))
            continue

        # ---------------------------------------------------------------------

        parsing_starttimep = datetime.now()
        cmdline.print_cmdline("#" * 48)
        cmdline.print_cmdline("Parsing points in {0}".format(filepath))

        # ---------------------------------------------------------------------

        trkpts, trklines, firsttimestamp, lasttimestamp, wpts, seg_uuids = \
            gpx.extractpoints(filepath, get_loc_func, False)

        # ---------------------------------------------------------------------

        seg_dict = db.insert_segments(cursor, seg_uuids)

        # ---------------------------------------------------------------------

        msg = "File first timestamp: {0}, last timestamp: {1}"
        cmdline.print_cmdline(msg.format(firsttimestamp, lasttimestamp))

        if firsttimestamp == 0 or lasttimestamp == 0:
            continue
            cmdline.print_cmdline("Skipping importing {0}.".format(filepath))

        # ---------------------------------------------------------------------

        parsing_endtime = datetime.now()
        parsing_duration = parsing_endtime - parsing_starttimep
        msg = "\nParsing {0} points and {1} waypoints from gpx file took {2}"
        cmdline.print_cmdline(
            msg.format(len(trkpts), len(wpts), parsing_duration))

        # ---------------------------------------------------------------------

        db_starttime = datetime.now()

        # print "Entering file into database"
        db.enterfile(filepath, cursor, userid, firsttimestamp, lasttimestamp)

        file_uid = db.get_currentfileid(cursor)

        # print "Entering points into database"
        db.enterpoints(cursor, userid, trkpts, file_uid, seg_dict)

        # print "Entering lines into database"
        db.enterlines(cursor, userid, trklines, file_uid, seg_dict)

        # print entering waypoints into database
        db.enterwaypoints(cursor, userid, wpts, file_uid)

        # ---------------------------------------------------------------------

        conn.commit()

        # ---------------------------------------------------------------------
        db_endtime = datetime.now()
        db_duration = db_endtime - db_starttime
        msg = "Entering into database took {0}"
        cmdline.print_cmdline(msg.format(db_duration))

        # ---------------------------------------------------------------------

    cursor.close()
    conn.close()

    endtime = datetime.now()
    cmdline.print_cmdline("#" * 48)
    cmdline.print_cmdline("Script took {0}\n".format(endtime - starttime))


def main():
    parser = argparse.ArgumentParser(prog='gpx2spatialite')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {0}'.format(__version__))

    subparsers = parser.add_subparsers(title='subcommands')
    parser_importer = subparsers.add_parser(
        'import', help='Import gpx files into a spatialite database')
    parser_create_db = subparsers.add_parser(
        'create_db', help='Create a new database')
    parser_update_locs = subparsers.add_parser(
        'update_locs', help='Update location infromation')
    parser_citydefs = subparsers.add_parser(
        'citydefs', help='Import/export citydefs file')

    parser_importer.add_argument('-d', '--database', dest='dbpath',
                                 metavar='FILE', required=True,
                                 help='Define path to saptialite database')
    parser_importer.add_argument('-u', '--user', dest='user', metavar='NAME',
                                 required=True, help='User name')
    parser_importer.add_argument('-s', '--skip-locations', dest='skip_locs',
                                 default=False, action='store_true',
                                 help='Skip querying locations for points \
                               (faster)')
    parser_importer.add_argument('-q', '--quiet', dest='quiet', default=False,
                                 action='store_true')
    parser_importer.add_argument('gpx_files', nargs='+', metavar='input-files',
                                 help='/path/to/gpx-file.gpx or \
                                 /path/to/folder')
    parser_importer.set_defaults(func=importer)

    parser_create_db.add_argument('-c', '--custom-citydefs',
                                  dest='custom_citydefs',
                                  metavar='SQL-SCRIPT',
                                  help='Set the citydefs sql file')
    parser_create_db.add_argument('-n',
                                  '--no-citydefs',
                                  dest='no_citydefs',
                                  action='store_true',
                                  default=False,
                                  help='Do not run the citydefs insert script')
    parser_create_db.add_argument('-e',
                                  '--execute-script',
                                  dest='execute_script',
                                  metavar='SQL-SCRIPT',
                                  help='Set an SQL script to run')
    parser_create_db.add_argument('new_dbpath',
                                  metavar='new-database',
                                  help='/path/to/new/database.sqlite')
    parser_create_db.set_defaults(func=create_db)

    parser_update_locs.add_argument('-a',
                                    '--all-locations',
                                    dest='all_locs',
                                    default=False,
                                    action='store_true',
                                    help='Scan all points and reset location,\
                                    not just unknown ones')
    parser_update_locs.add_argument('-q',
                                    '--quiet',
                                    dest='quiet',
                                    default=False,
                                    action='store_true')
    parser_update_locs.add_argument('dbpath',
                                    metavar='database',
                                    help='/path/to/database.sqlite')
    parser_update_locs.set_defaults(func=update_locs)

    parser_citydefs.add_argument('-q',
                                 '--quiet',
                                 dest='quiet',
                                 default=False,
                                 action='store_true')
    group_c = parser_citydefs.add_mutually_exclusive_group(required=True)
    group_c.add_argument('-e',
                         '--export',
                         metavar='SQL-FILE',
                         dest='export_citydefs',
                         help='Export citydefs')
    group_c.add_argument('-i',
                         '--import',
                         metavar='SQL-FILE',
                         dest='import_citydefs',
                         help='Import citydefs')
    parser_citydefs.add_argument('dbpath',
                                 metavar='database',
                                 help='/path/to/database.sqlite')
    parser_citydefs.set_defaults(func=citydefs)

    # -------------------------------------------------------------------------
    # when there is no subcommand add default to arguments list
    if (len(sys.argv) > 1
            and '-h' not in sys.argv
            and '--help' not in sys.argv
            and '--version' not in sys.argv):
        subparser_found = False
        for subaction in subparsers._get_subactions():
            if sys.argv[1] == subaction.dest:
                subparser_found = True
                break
        if not subparser_found:
            sys.argv.insert(1, 'import')

    # -------------------------------------------------------------------------

    args = parser.parse_args()
    args.func(vars(args))


if __name__ == '__main__':
    main()
