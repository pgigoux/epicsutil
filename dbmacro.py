#!/usr/bin/python
"""
This program is used to list or replace macro references in a database file
The standard input is used if no files are specified.
The records are listed in the same order as they appear in the database file.
"""
import sys
from argparse import ArgumentParser, SUPPRESS, Namespace
from db import EpicsMacro
from files import process_file_list

# Used to control printing of debug output.
debug_flag = False


def replace_macros(f, file_name, p_args):
    """
    Replace macro references with its value.
    Values are extracted from the macro defined in the command line
    This is the callback function for process_file_list.
    It will get called once for each file in the input file list.
    :param f: database file
    :param file_name: file name (not used)
    :param p_args: command line arguments
    :return: None
    """
    if debug_flag:
        print('\n-- replace_macros', f, file_name, p_args)

    m = EpicsMacro(p_args.macros, add_undefined=p_args.undefined)

    for line in f:
        line = line.rstrip()
        try:
            line = m.replace_macros(line, report_undefined=True)
        except KeyError as ex:
            print('# -- ' + str(ex))
        print(line)

    return


def list_macros(f, file_name, p_args):
    """
    List all macros found in a database, one per line.
    :param f: database file
    :param file_name: file name (not used)
    :param p_args: command line arguments (not used)
    :return: None
    """
    if debug_flag:
        print('\n-- list_macros', f, file_name, p_args)

    m = EpicsMacro(p_args.macros)

    # Look for macros in all lines
    output_set = set()
    for line in f:
        output_set |= set(m.get_macros(line.rstrip()))

    # Print the output set
    for macro_name in output_set:
        print(macro_name)

    return


def get_args(argv):
    """
    Process command line arguments
    :param argv: command line arguments from sys.argv
    :type argv: list
    :return: arguments
    :rtype: Namespace
    """

    # The following text is used as epilog (footer) in the help output
    epilog_text = """The standard input is used if no files are supplied""" + \
                  """. A macro substitution is defined using two words (name and value) after the -m option""" + \
                  """. Any number of macro substitutions can be specified in the command line """

    parser = ArgumentParser(epilog=epilog_text)

    parser.add_argument(action='store',
                        nargs='*',
                        dest='files',
                        default=[])

    parser.add_argument('-l', '--list',
                        action='store_true',
                        dest='list_flag',
                        default=False,
                        help='list macros')

    parser.add_argument('-m', '--macro',
                        action='append',
                        nargs=2,
                        dest='macros',
                        default=[],
                        help='macros to substitute')

    parser.add_argument('-u', '--undefined',
                        action='store_true',
                        dest='undefined',
                        default=False,
                        help='automatically add ",undefined" macros to the macros to subtitute')

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    return parser.parse_args(argv[1:])


if __name__ == '__main__':
    try:
        # Test code
        # args = get_args(['dbmacro',
        #                  'rtc/rtcTop.db-test',
        #                  '-m', 'top', 'RTC',
        #                  '-m', 'aom', 'AOM',
        #                  '-m', 'tcs', 'TCS',
        #                  '-m', 'myst', 'MYST',
        #                  '-m', 'cr', 'CR',
        #                  '-m', 'NELM', '20280'])
        # args = get_args(['dbmacro', '-l', 'rtc/rtcTop.db-orig', 'rtc/rtcMystTop.db-orig', 'rtc/rtcTv.db-orig'])
        # args = get_args(['dbmacro',
        #                  '--debug',
        #                  '-m', 'top', 'aom:',
        #                  '-m', 'aom', 'aom:',
        #                  '-m', 'tcs', 'tcs:',
        #                  '-m', 'rtc', 'rtc:',
        #                  '-m', 'oiwfs', 'aom:oiwfs:',
        #                  '-m', 'omstype', 'OMS 58 VME',
        #                  'data/aom/aomTop.db_orig'])
        # args = get_args(['dbmacro',
        #                  '--debug',
        #                  '-m', 'top', 'mac:',
        #                  '-m', 'mech', 'bolt:',
        #                  '-m', 'sys', 'rocket:',
        #                  '-m', 'dev', 'wing:',
        #                  'test_data/macro.db'])
        # args = get_args(['dbmacro', '--debug', '-l', 'test_data/macro.db'])

        args = get_args(sys.argv)
        debug_flag = args.debug
        if debug_flag:
            print(args)
        if args.list_flag:
            process_file_list(args.files, list_macros, args=args)
        elif args.macros:
            process_file_list(args.files, replace_macros, args=args)
        else:
            print('No macros to substitute')

    except Exception as e:
        print(e)
        sys.exit(1)
