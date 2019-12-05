#!/usr/bin/python
import sys
from argparse import ArgumentParser, SUPPRESS
from pvparser import PvParser

if __name__ == '__main__':
    """
    Entry point for the pvload check program.
    """

    # Command line arguments
    parser = ArgumentParser(epilog='')

    parser.add_argument(action='store',
                        nargs='*',
                        dest='file_list',
                        default=[],
                        help='list of input files')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        dest='verbose',
                        default=False)

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    args = parser.parse_args(sys.argv[1:])

    pv_parser = PvParser(args.debug, args.verbose)
    # pv_parser.set_debug(args.debug)

    for file_name in args.file_list:
        pv_parser.pv_file(file_name)
