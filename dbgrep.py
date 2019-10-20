#!/usr/bin/python
"""
This program is the equivalent of the grep command in Unix, but designed to search
for strings in database files taking into account the database file structure.
It will list those records where a match is found in the record name, field name
and field value. By default, the record name is printed before the field matches found.

The input should be a valid database file. The output will have a valid database syntax.
This was done so the output of the dbgrep can be piped to other database utilities.

It is possible to match for record name, record type, field name or field value.
All the matching options will be true if none is specified.

Matching is an OR operation, i.e. using more than one option will print records that match one the other.
An AND matching can be achieved by piping the output from one dbgrep instance to another.

The following rules are used when matching:
* The record header and end are printed when matching for record name or type is selected.
* The record header and end are printed when a match in a field name or value is found for that record.
* All fields are printed when matching for record name or type is selected, and matching by field name or value is not
* Only matching fields are printed when matching by field name or value is selected.
* The file name will be printed as a comment ('#') when the file name option is selected or
  when greping more than one file

"""
import sys
import re
from argparse import ArgumentParser, SUPPRESS, Namespace
from files import process_file_list
from db import DatabaseFile, EpicsRecord
from db import format_record_start, format_record_end, format_field

# Variable used to control printing of debug output.
# A global variable was used for code readability.
debug_flag = False


def file_name_header(file_name):
    """
    Format file name for printing as a comment in the output
    :param file_name: file name
    :type file_name: str
    :return: file name header
    :rtype: str
    """
    return '#' + '-' * 50 + '\n# File: ' + file_name + '\n#' + '-' * 50


def print_all_fields(record):
    """
    Print all fields in a record
    :param record: record
    :type record: EpicsRecord
    :return:
    """
    for field_name, field_value in record.get_fields():
        print(format_field(field_name, field_value))
    return


def grep_file(f, file_name, p_args):
    """
    This routine looks for matches in the record name, record type, field name and/or field value.
    The command line options are used to select what type of matching is desired.
    The output will have a valid database syntax.
    :param f: database file
    :param file_name: database file name
    :param p_args: command line arguments
    :type p_args: Namespace
    """

    # Print debug information
    if debug_flag:
        print(file_name, p_args.pattern, file_name)

    # This variable is used to control whether the file name should be printed embedded in the
    # output database as a comment. When no matches are found no file name should be printed not
    # be printed to avoid unwanted output.
    more_than_one_file = True if len(p_args.files) > 1 else False

    # The following variable controls whether only the file name should be printed when a match is found
    # Flags to control the output
    file_name_only = p_args.filename

    # This variable is usd to control whether all the fields in a matching record
    # should be printed when a match is found.
    all_fields = p_args.all_fields

    if debug_flag:
        print('more_than_one_file, file_name_only =', more_than_one_file, file_name_only)

    # Compile the pattern to make sure that there are no errors in it.
    # This will speed up searches and will catch errors before processing files.
    try:
        p = re.compile(p_args.pattern, re.IGNORECASE if p_args.ignorecase else 0)
    except Exception as ex:
        print('Error while parsing regular expression', ex)
        return

    # Create the database file object
    df = DatabaseFile(f)
    if debug_flag:
        print(df)

    # Match field name or value?
    match_fields = p_args.field_name or p_args.field_value

    # Used to break out from two nested loops (Python doesn't have labeled breaks yet).
    break_out = False

    # Loop over all records in the file.
    # The records will be processed in the same order as in the file.
    for record in df.next_record():
        assert (isinstance(record, EpicsRecord))

        # This variable is used to determine whether the start of a record was printed or not.
        # We only need the record name once per record. A match in a field name or value will
        # print the record start if it was not printed already.
        record_start_printed = False

        # Get record and type
        record_name, record_type = record.get_name(), record.get_type()
        if debug_flag:
            print(record_name, record_type)

        # Check whether matching for record name and type is selected
        # Print the record header if there's a record match
        if (p_args.record_name and p.search(record_name)) or (p_args.record_type and p.search(record_type)):

            # Print the file name and stop looking for more matches
            if file_name_only:
                print(file_name)
                break

            # Print a file header as comment if there are more than one input files
            if more_than_one_file:
                print(file_name_header(file_name))
                more_than_one_file = False  # file name header was printed

            # Print the record start and mark it as printed
            print(format_record_start(record_name, record_type))
            record_start_printed = True  # record start was printed

            # If printing all fields then don't bother checking for matching fields
            if all_fields:
                print_all_fields(record)
                print(format_record_end())
                continue

        # Match fields?
        if match_fields:
            for field_name, field_value in record.get_fields():

                # Check matching for field name and/or value
                if (p_args.field_name and p.search(field_name)) or (p_args.field_value and p.search(field_value)):

                    # Print the file name and stop looking for more matches
                    if file_name_only:
                        print(file_name)
                        break_out = True  # stop record loop
                        break

                    # The record start and file header should be printed if it was done already.
                    if not record_start_printed:
                        if more_than_one_file:
                            print(file_name_header(file_name))
                            more_than_one_file = False  # file name was printed
                        print(format_record_start(record_name, record_type))
                        record_start_printed = True  # record start was printed

                    # If printing all fields then break the loop and continue with the next record
                    if all_fields:
                        print_all_fields(record)
                        break
                    else:
                        print(format_field(field_name, field_value))

            # Break out from the record loop
            if break_out:
                break

        # Print the record end if the start was printed
        if record_start_printed:
            print(format_record_end())

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
    epilog_text = """The standard input is used if no input files are specified.""" + \
                  """ The program will look for matches in the record name, record type,""" + \
                  """ field name and field value if no matching options are specified."""

    parser = ArgumentParser(epilog=epilog_text)

    parser.add_argument('-i', '--ignorecase',
                        action='store_true',
                        dest='ignorecase',
                        default=False,
                        help='ignore case')

    parser.add_argument('-r', '--recordname',
                        action='store_true',
                        dest='record_name',
                        default=False,
                        help='match record name only')

    parser.add_argument('-t', '--recordtype',
                        action='store_true',
                        dest='record_type',
                        default=False,
                        help='match record type only')

    parser.add_argument('-f', '--fieldname',
                        action='store_true',
                        dest='field_name',
                        default=False,
                        help='match field name only')

    parser.add_argument('-v', '--fieldvalue',
                        action='store_true',
                        dest='field_value',
                        default=False,
                        help='match field value only')

    parser.add_argument('-a', '--allfields',
                        action='store_true',
                        dest='all_fields',
                        default=False,
                        help='print all fiels in a record when there is a match')

    parser.add_argument('-l', '--filename',
                        action='store_true',
                        dest='filename',
                        default=False,
                        help='print file names only')

    parser.add_argument(action='store',
                        dest='pattern',
                        default='')

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
        # Test code
        # args = get_args(['dbgrep', 'mem', 'data/diff1.db', '-r', '--ignore', '--debug'])
        # args = get_args(['dbgrep', '-r', '-t', 'longin', 'test_data/diff1.db', 'test_data/diff2.db'])
        # args = get_args(
        #     ['dbgrep', 'botS|hrwfs:', 'test_data/ag_top.db', 'test_data/aomTop.db',
        #      'test_data/ecs.db', 'test_data/simu_top.db'])
        # args = get_args(['dbgrep', '--debug', 'field', 'test_data/ag_sadtop.db'])
        # args = get_args(['dbgrep', 'gis', 'test_data/grep1.db', '--ignore'])

        args = get_args(sys.argv)
        debug_flag = args.debug
        if debug_flag:
            print(args)

        # By default all search options are false.
        # Make all search options true if all of them are false.
        if True not in (args.record_name, args.record_type, args.field_name, args.field_value):
            (args.record_name, args.record_type, args.field_name, args.field_value) = (True, True, True, True)
        if debug_flag:
            print(args.record_name, args.record_type, args.field_name, args.field_value)

        process_file_list(args.files, grep_file, args=args)

    except Exception as e:
        print(e)
        sys.exit(1)
