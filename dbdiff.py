#!/usr/bin/env python
"""
Print the difference between two database files.
It checks for the following possible differences:
(1) Records that are present only in one of the input files
(2) Records common to the two input files that have a different record type
(3) Fields that are not common for the same record
(4) Differences in the field values
"""
import sys
import os
import time
import subprocess
from argparse import ArgumentParser, SUPPRESS, Namespace
from db import DatabaseFile, EpicsDatabase, EpicsMacro, FILTER_RECORD, FILTER_FIELD

# Indentation used when printing differences
FIRST_INDENT = ' ' * 2
SECOND_INDENT = ' ' * 5

# Name of the directory where (temporary) sorted files will be written to
TEMP_DIRECTORY = os.path.join(os.path.sep, 'tmp')
# TEMP_DIRECTORY = './tmp'

# Variable used to control printing of debug output.
# A global variable was used for code simplicity.
debug_flag = False

# Variable used to store the EpicsMacro object used for macro substitution in diff_filter.
# A global variable is the easiest/cleanest way of passing the object to the routine.
diff_macros = None


def diff_filter(what, name, attribute):
    """
    Callback routine that will be called by the database routines to filter
    record names, record types, field names and field values.
    It filters out record differences that are introduced by the tools used to
    compile the schematics and/or different versions of EPICS.
    Leading and trailing whitespaces are trimmed out.
    :param what: what to filter (record of field)
    :type what: int
    :param name: record name or field name
    :type name: str
    :param attribute: record type or field value
    :type attribute: str
    :return: tuple containing the filtered name and attribute
    :rtype tuple
    """
    if what == FILTER_RECORD:
        output_name = name if diff_macros is None else diff_macros.replace_macros(name)
        return output_name.strip(), attribute.strip()
    elif what == FILTER_FIELD:
        output_attr = attribute if diff_macros is None else diff_macros.replace_macros(attribute)
        output_attr = output_attr.replace('.NPP', 'NPP')
        output_attr = output_attr.replace('.PP', 'PP')
        output_attr = output_attr.replace('.CPP', 'CPP')
        output_attr = output_attr.replace('.CP', 'CP')
        output_attr = output_attr.replace('.NMS', ' NMS')
        output_attr = output_attr.replace('.MS', ' MS')
        # Handle description differences between different versions of EPICS
        if name == 'DESC':
            output_attr = output_attr.replace('Gemini ', '')
            output_attr = output_attr.replace('status record', 'Status Record')
        # output_attr = output_attr.replace('Gemini Status Record', 'status record')
        return name.strip(), output_attr.strip()
    else:
        # this should never happen
        raise(ValueError, 'Unknown what to filter value')


def print_only_in_one(record_name_list, file_name):
    """
    Auxiliary function to print records present in only one database.
    The main purpose of this function is to avoid duplication of code.
    :param record_name_list: list of record names
    :type record_name_list: list
    :param file_name: database file name (for message)
    :type file_name: str
    :return: None
    """
    if debug_flag:
        print('\n-- print_only_in_one', record_name_list, file_name)
    if len(record_name_list):
        print('\nRecords only in', file_name)
        for record_name in sorted(record_name_list):
            print(FIRST_INDENT, record_name)


def print_record_type_differences(record_name_list):
    """
    Auxiliary routine to print the list of records that have the same name and different type.
    The main purpose of this function is to improve code readability.
    :param record_name_list: list of record names that have different type
    :type record_name_list: list
    :return: None
    """
    if debug_flag:
        print('\n-- print_record_type_differences', record_name_list)
    section_title = True
    for record_name in sorted(record_name_list):
        if section_title:
            print('\nRecords that are of different type')
            section_title = False
        print(FIRST_INDENT, record_name)


def print_field_name_differences(db1, db2, record_name_list):
    """
    Auxiliary routine to print the list fields in all records that are present
    only in one of the instances of the same record. This routine is intended to
    detect the following cases:
    (1) misspelled field names (typos)
    (2) missing fields because of editing with two different tools
    (3) corrupted databases
    :param db1: database 1
    :param db1: EpicsDatabase
    :param db2: database 2
    :type db2: EpicsDatabase
    :param record_name_list: list of record names common to the two databases with the same type
    :type record_name_list: list
    :return: None
    """
    if debug_flag:
        print('\n-- print_field_name_differences', db1, db2, record_name_list)

    section_title = True
    for record_name in sorted(record_name_list):
        # field_names_in_1 = set(db1[record_name].keys())
        # field_names_in_2 = set(db2[record_name].keys())
        field_names_in_1 = set(db1.get_record(record_name).get_field_names())
        field_names_in_2 = set(db2.get_record(record_name).get_field_names())
        # print field_names_in_1
        non_common_fields = field_names_in_1 ^ field_names_in_2
        if len(non_common_fields):
            if section_title:
                print('\nFields that are not common in the same record')
                section_title = False
            print(FIRST_INDENT, record_name + ':', ' '.join(non_common_fields))


def print_field_value_differences(db1, db2, record_name_list):
    """
    Print differences in the value of fields for the same record.
    This is the most common case of database differences in a project.
    :param db1: database 1
    :param db1: EpicsDatabase
    :param db2: database 2
    :type db2: EpicsDatabase
    :param record_name_list: list of record names common to the two databases with the same type
    :type record_name_list: list
    :return:
    """
    if debug_flag:
        print('\n-- print_field_value_differences', db1, db2, record_name_list)

    section_title = True
    for record_name in sorted(record_name_list):
        field_names_in_1 = set(db1.get_record(record_name).get_field_names())
        field_names_in_2 = set(db2.get_record(record_name).get_field_names())
        record_title = True
        for field_name in sorted(field_names_in_1 & field_names_in_2):
            value_1 = db1.get_record(record_name).get_field_value(field_name)
            value_2 = db2.get_record(record_name).get_field_value(field_name)
            # print record_name, field_name, value_1, value_2
            if value_1 != value_2:
                if section_title:
                    print('\nDifferences in field values')
                    section_title = False
                if record_title:
                    print(FIRST_INDENT, 'in', record_name)
                    record_title = False
                    print(SECOND_INDENT, field_name, '"' + value_1 + '"', '"' + value_2 + '"')

    return


def diff_databases(df1, df2, file_name1, file_name2):
    """
    Determine the differences between two databases files.
    This is the routine where the actual work is done.
    A diff using the logical structure of the files instead of a
    plain text diff.
    :param df1: file handle 1
    :type df1: DatabaseFile
    :param df2: file handle 2
    :type df2: DatabaseFile
    :param file_name1: file name 1 (for messages)
    :type file_name1: str
    :param file_name2: file name 2 (for messages)
    :type file_name2: str
    :return:
    """
    if debug_flag:
        print('\n-- print_field_value_differences', df1, df2, file_name1, file_name2)

    try:
        db1 = df1.read_database()
        db2 = df2.read_database()
    except Exception as ex:
        print(ex)
        return

    # These are here to help PyCharm with the object types
    # TODO: check whether this is still true
    assert (isinstance(db1, EpicsDatabase))
    assert (isinstance(db2, EpicsDatabase))

    # Use set operations and list comprehensions to efficiently determine
    # what records are common to the two databases, what records of the common
    # set have the same and different types, and what records are present in
    # only one of the databases
    record_names_in_1 = set(db1.get_record_names())
    record_names_in_2 = set(db2.get_record_names())
    common_record_names = record_names_in_1 & record_names_in_2
    # common_record_types = set([r for r in common_record_names if db1[r][TYPE_KEY] == db2[r][TYPE_KEY]])
    common_record_types = set(
        [r for r in common_record_names if db1.get_record(r).get_type() == db2.get_record(r).get_type()])
    different_record_types = common_record_names ^ common_record_types
    only_in_1 = common_record_names ^ record_names_in_1
    only_in_2 = common_record_names ^ record_names_in_2

    # Handy debug code
    if debug_flag:
        print('database 1:  ', sorted(record_names_in_1))
        print('database 2:  ', sorted(record_names_in_2))
        print('common names:', sorted(common_record_names))
        print('common types:', sorted(common_record_types))
        print('diff. types: ', sorted(different_record_types))
        print('only in 1:   ', sorted(only_in_1))
        print('only in 2:   ', sorted(only_in_2))
        print('\n')

    # Print records present in only one of the databases
    print_only_in_one(list(only_in_1), file_name1)
    print_only_in_one(list(only_in_2), file_name2)

    # Print records that have different type
    print_record_type_differences(list(different_record_types))

    # Print field name and field type mismatches for the same record
    # These routines require the list of records with common types as argument
    print_field_name_differences(db1, db2, list(common_record_types))
    print_field_value_differences(db1, db2, list(common_record_types))

    return


def diff_files_internal(file_name1, file_name2, p_args):
    """
    Open the two database files and call the the internal difference function
    :param file_name1: file name 1
    :type file_name1: str
    :param file_name2: file name 2
    :type file_name2: str
    :param p_args: command line arguments
    :type p_args: Namespace
    :return:
    """
    if debug_flag:
        print('\n-- diff_databases', file_name1, file_name2)
    try:
        # f1 = open(file1, 'r')
        # f2 = open(file2, 'r')
        # diff_databases(f1, f2, file1, file2)
        my_filter = diff_filter if p_args.clean else None
        df1 = DatabaseFile(file_name=file_name1, filter_function=my_filter)
        df2 = DatabaseFile(file_name=file_name2, filter_function=my_filter)
        diff_databases(df1, df2, file_name1, file_name2)
        df1.close()
        df2.close()
    except (OSError, IOError) as ex:
        print(ex)


def diff_files_external(file_name1, file_name2, p_args):
    """
    Open the two database files, sort them and call the external difference program.
    :param file_name1: file name 1
    :param file_name2: file name 2
    :param p_args: command line arguments
    :return: None
    """
    # Read databases into memory
    try:
        my_filter = diff_filter if p_args.clean else None
        df1 = DatabaseFile(file_name=file_name1, filter_function=my_filter)
        df2 = DatabaseFile(file_name=file_name2, filter_function=my_filter)
        db1 = df1.read_database()
        db2 = df2.read_database()
        df1.close()
        df2.close()
    except (OSError, IOError) as ex:
        print(ex)
        return

    # Create output file names by appending a time stamp
    time_stamp = str(int(time.time()))
    output_file_name1 = os.path.join(TEMP_DIRECTORY, os.path.basename(file_name1) + '_' + time_stamp + '_1')
    output_file_name2 = os.path.join(TEMP_DIRECTORY, os.path.basename(file_name2) + '_' + time_stamp + '_2')

    # Write the sorted databases to disk
    for db, file_name in [(db1, output_file_name1), (db2, output_file_name2)]:
        # print db, file_name
        assert (isinstance(db, EpicsDatabase))
        try:
            f = open(file_name, 'w')
            db.write_sorted_database(f_out=f)
            f.close()
        except (OSError, IOError) as ex:
            print(ex)
            return

    # Call external program to diff the files
    external_program = p_args.program[0]
    print('calling', external_program, 'with', output_file_name1, 'and', output_file_name2)
    try:
        subprocess.call([external_program, output_file_name1, output_file_name2])
    except subprocess.CalledProcessError as ex:
        print('error while calling' + external_program)
        print(ex)

    # Remove temporary files
    try:
        os.remove(output_file_name1)
        os.remove(output_file_name2)
    except OSError as ex:
        print(ex)

    return


def diff_files(file_name1, file_name2, p_args):
    """
    Open the two database files and call the the diff function
    :param file_name1: file name 1
    :param file_name2: file name 2
    :param p_args: command line arguments
    :return:
    """
    if p_args.program:
        diff_files_external(file_name1, file_name2, p_args)
    else:
        diff_files_internal(file_name1, file_name2, p_args)


def get_args(argv):
    """
    Process command line arguments
    :param argv: command line arguments from sys.argv
    :type argv: list
    :return: arguments
    :rtype: Namespace
    """

    parser = ArgumentParser()

    parser.add_argument(action='store',
                        nargs=2,
                        dest='input_file',
                        help='input file',
                        default=[])

    parser.add_argument('-p', '--program',
                        action='store',
                        nargs=1,
                        dest='program',
                        help='external program to do the diff [default=none]',
                        default='')

    parser.add_argument('-c', '--clean',
                        action='store_true',
                        dest='clean',
                        default=False,
                        help='clean up differences with legacy databases')

    parser.add_argument('-m', '--macro',
                        action='append',
                        nargs=2,
                        dest='macros',
                        default=[],
                        help='macros to substitute')

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    return parser.parse_args(argv[1:])


if __name__ == '__main__':
    try:
        # args = get_args(['dbdiff', 'test_data/diff1.db', 'test_data/diff2.db', '--debug'])
        # args = get_args(['dbdiff', 'test_data/diff1.db', 'test_data/diff2.db'])
        # args = get_args(['dbdiff', '-c', '-m', 'top', 'cr:', 'test_data/crtop_legacy.db', 'test_data/crtop_rtems.db'])

        args = get_args(sys.argv)
        debug_flag = args.debug
        if args.macros:
            diff_macros = EpicsMacro(args.macros, add_undefined=True)
        if debug_flag:
            print(args)
        diff_files(args.input_file[0], args.input_file[1], args)
    except Exception as e:
        print(e)
        sys.exit(1)
