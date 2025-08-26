#!/usr/bin/env python
"""
Sort records and fields in a list of database files.
Each file is sorted separately. Fields are sorted within each record.
This program is intended to compare database with diff or meld.
"""
import sys
from io import TextIOBase
from argparse import ArgumentParser, SUPPRESS, Namespace
from files import process_file_list
from db import DatabaseFile, EpicsDatabase

# Variable used to control printing of debug output.
debug_flag = False


def sort_database(f, file_name, p_args):
    """
    This is the callback function for process_file_list.
    Read the database file and print the database sorted by record and field names.
    :param f: database file
    :type f: TextIOBase
    :param file_name: file name (needed, but not used)
    :type file_name: str
    :param p_args: command line arguments (not used)
    :type p_args: Namespace
    :return: None
    """
    if debug_flag:
        print('\n-- sort_database', f, file_name, p_args)
    df = DatabaseFile(f)
    db = df.read_database()
    assert (isinstance(db, EpicsDatabase))
    db.write_sorted_database(reverse=p_args.reverse)
    df.close()
    return


def get_args(argv):
    """
    Process command line arguments
    :param argv: command line arguments from sys.argv
    :type argv: list
    :return: arguments
    :rtype: Namespace
    """

    parser = ArgumentParser(epilog='Files are sorted individually. The standard input is used if no files are supplied')

    parser.add_argument('-r', '--reverse',
                        action='store_true',
                        dest='reverse',
                        default=False,
                        help='reverse sort order')

    parser.add_argument(action='store',
                        nargs='*',
                        dest='files',
                        default=[])

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    return parser.parse_args(argv[1:])


if __name__ == '__main__':
    try:
        # args = get_args(['dbsort', 'data/diff1.db', '--debug', '--reverse'])
        args = get_args(sys.argv)
        debug_flag = args.debug
        if debug_flag:
            print(args)
        process_file_list(args.files, sort_database, args=args)
    except Exception as e:
        print(e)
        sys.exit(1)
