#!/usr/bin/env python
"""
This program replicates the behaviour of the dbl command in EPICS.
It takes a list of input files and lists the records in each file.
The standard input is used if no files are specified.
The records are listed in the same order as they appear in the database file.
"""
import sys
from argparse import ArgumentParser, SUPPRESS, Namespace
from files import process_file_list
from db import DatabaseFile

# Used to control printing of debug output.
debug_flag = False


def list_records(f, file_name, p_args):
    """
    This is the callback function for process_file_list.
    It will get called once for each file in the input file list.
    List records in a database file.
    :param f: database file
    :param file_name: file name (not used)
    :param p_args: command line arguments
    :return: None
    """
    if debug_flag:
        print('\n--list_records', f, file_name, p_args)
    df = DatabaseFile(f)
    for record_name, record_type in df.next_record_name():
        if p_args.type:
            print(record_name + ', ' + record_type)
        else:
            print(record_name)
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

    parser = ArgumentParser(epilog='The standard input is used if no files are supplied')

    parser.add_argument(action='store',
                        nargs='*',
                        dest='files',
                        default=[])

    parser.add_argument('-t', '--type',
                        action='store_true',
                        dest='type',
                        default=False,
                        help='print record type')

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    return parser.parse_args(argv[1:])


if __name__ == '__main__':
    try:
        # args = get_args(['dbl', 'data/diff1.db', '--type'])
        # args = get_args(['dbl', 'data/diff1.db', '--type', '--debug'])
        # args = get_args(['dbl', 'rtc/rtcUsrTop.db'])
        args = get_args(sys.argv)
        debug_flag = args.debug
        if debug_flag:
            print(args)
        process_file_list(args.files, list_records, args=args)
    except Exception as e:
        print(e)
        sys.exit(1)
