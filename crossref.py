#!/usr/bin/env python3
"""
Look for database references between systems.

The program requires the databases to be placed in a directory with one subdirectory per systems.

For a given system, the program will print the references to records in other systems and
the references from other systems' databases.

Databases that use macros in records names should have them replaced by the actual values or
the program will most likely fail to find cross references (use dbmacro for macro replacement).

The program creates a directory with index files to speed up searches the first time it's executed.
These indices should be rebuilt in the database files are updated (--rebuild option).
"""
import sys
import re
from os import listdir, makedirs
from os.path import exists, isfile, isdir, join, splitext
from argparse import ArgumentParser, SUPPRESS
from db import DatabaseFile, EpicsRecord, EpicsMacro

# Default directory where databases are stored
DEFAULT_DATABASE_DIRECTORY = join('.', 'data')

# Default directory where indices are stored
DEFAULT_INDEX_DIRECTORY = join('.', 'indices')

# This regular expression used to rule out strings that don't match a record name
# It only needs to be good enough to check whether a string looks like a record name.
# The pattern is precompiled to speed up matching in the program.
RECORD_NAME_PATTERN = r'^[a-zA-Z0-9]+\:'
compiled_pattern = re.compile(RECORD_NAME_PATTERN)


# -------------------------------------------------------------------------
# Auxiliary routines
# -------------------------------------------------------------------------

def get_index_file_name(system, index_directory):
    """
    Return the index file name for a given system.
    Provided to remove code duplication.
    :param system: system name
    :type system: str
    :param index_directory: index directory
    :type index_directory: str
    :return: index file name
    :rtype: str
    """
    return join(join(index_directory, system) + '.index')


def get_database_names(system, data_directory):
    """
    Return the list of database files for a given system.
    There should be a directory with the system's name in the data directory.
    It does not check for the existence of the data directory.
    :param system: system name
    :type system: str
    :param data_directory: data directory
    :type data_directory: str
    :return:
    """
    return [join(data_directory, system, f) for f in listdir(join(data_directory, system)) if re.search(r'\.db$', f)]


def filtered_field_value(value):
    """
    Returned the filtered value for a record field by removing
    quotes and additional data (e.g. .PP) from the field value.
    :param value: field value (potentially more than one word)
    :type value: str
    :return: filtered field value (first word)
    :rtype: str
    """
    # return re.sub('"', '', str(value.split()[0].split('.')[0])).strip()
    return re.sub('"', '', str(value.split()[0])).strip()


def get_system_list(data_directory):
    """
    Return the list of systems found in the data directory.
    There should be one directory per system containing all the databases for that system.
    Ignore files that are not a directory.
    :param data_directory:
    :return:
    """
    return [f for f in listdir(data_directory) if isdir(join(data_directory, f))]


def parse_field_value(field_value):
    """
    Extract field value from the field value string.
    It just filters double quotes and extract the first word from the value.
    This is not a full proof way, but it's good enough for want we want.
    :param field_value: raw field value from the database
    :type field_value: str
    :return: record and field name (tuple)
    :rtype: tuple
    """
    try:
        filtered_value = re.sub('"', '', str(field_value.split()[0])).strip()
        # print '[' + filtered_value + ']'
    except (IndexError, AttributeError):
        return None, None  # something is rotten in my kingdom

    # Check whether the filtered value "looks like" a record name.
    # If that's the case, split the record name and the field name.
    if compiled_pattern.search(filtered_value):
        lst = filtered_value.split('.')
        if len(lst) > 1:
            return lst[0], lst[1]
        else:
            return lst[0], 'VAL'  # field specification was missing, assume VAL
    else:
        return None, None  # not a record name


def print_sorted_dictionary(d):
    """
    Auxiliary routine used to print a dictionary sorted by key
    :param d: dictionary
    :return: nothing
    """
    for item in sorted(d):
        print(item, d[item])


def remove_duplicates(input_list):
    """
    Auxiliary routine called by system_to_others to remove entries that have duplicate
    channel names. Each element in the list is a tuple with three elements.
    The channel name is the firtst tuple element.
    :param input_list: list of tuples
    :type input_list: list
    :return: list without duplicate channel names
    :rtype: list
    """
    temp_list = []
    output_list = []
    for a, b, c in input_list:
        if a not in temp_list:
            output_list.append((a, b, c))
            temp_list.append(a)
    # print input_list
    return output_list


# -------------------------------------------------------------------------
# Routines that take care of building index files
# -------------------------------------------------------------------------

def read_subs_file(database_name):
    """
    Read the macro substitution file for a give database.
    It returns an EpicsMacro object with all the definitions in the file.
    :param database_name: database file name
    :type database_name: str
    :return: EpicsMacro object with macros definitions in the subs file
    :rtype: EpicsMacro
    """
    subs_filename = splitext(database_name)[0] + '.subs'
    # print(splitext(database_name)[0])
    # print subs_filename
    if exists(subs_filename):
        macro_list = []
        f = open(subs_filename, 'r')
        for line in f:
            line = line.strip().split()
            # print line
            macro_list.append(line)
        # print macro_list
        m = EpicsMacro(macro_list)
        # print m
        return m
    else:
        return None


def create_index_file(index_file_name, database_list):
    """
    Write the index (list of records) for a given system to a disk file.
    :param index_file_name: index file name
    :type index_file_name: str
    :param database_list: list of databases for the given system
    :type database_list: list
    :return:
    """
    record_name_list = []
    for database_name in database_list:
        print(database_name)

        # Open database and macro substitution file (if any)
        db = DatabaseFile(file_name=database_name)
        m = read_subs_file(database_name)

        # Create a list with all records in the databases
        record_name_list.extend([r[0] for r in db.next_record_name()])
        # print record_name_list

        # Substitute macros if the macro substitution file was defined.
        # There's no need to replace macros in the record fields since
        # only record names are written to the index files.
        if m is not None:
            record_name_list = [m.replace_macros(r) for r in record_name_list]

    # Write the index file
    f = open(index_file_name, 'w')
    f.write("\n".join(str(x.strip()) for x in record_name_list))
    f.close()


def build_indices(sys_list, data_directory, index_directory, rebuild):
    """
    Build the index files for each system in the input list.
    It creates the index directory and/or index file if they don't exist,
    or if the rebuild parameter is true.
    :param sys_list: list of systems
    :type sys_list: list
    :param data_directory: directory where database files are stored
    :type data_directory: str
    :param index_directory: directory where index files are stored/created
    :type index_directory: str
    :param rebuild: rebuild indices?
    :type rebuild: bool
    :return: dictionary with systems per channel
    :rtype: dict
    """
    # print index_directory

    # Make sure the index directory exists. Create it otherwise.
    # Raise an exception if the index directory cannot be created.
    if exists(index_directory):
        if isfile(index_directory):
            print('The index directory exists, but is a plain file')
            return None
    else:
        try:
            makedirs(index_directory)
        except Exception as e:
            print('Could not create index directory', str(e))
            return None

    channel_directory = {}

    # Loop over all systems
    for system in sys_list:

        # Get database file names for the system.
        # Skip systems with no databases and print a warning.
        database_list = get_database_names(system, data_directory)
        # print database_list
        if not database_list:
            print('No databases found for', system)
            continue

        # Check whether the index file needs to be rebuilt.
        # This can happen if it doesn't exist or if the rebuild flag is set.
        index_file_name = get_index_file_name(system, index_directory)
        if not exists(index_file_name) or rebuild:
            try:
                create_index_file(index_file_name, database_list)
                print('created index file', index_file_name)
            except Exception as e:
                print('Could not create index file for', system, str(e))
                continue

        # Check whether the index file exits.
        # Skip systems whose index file cannot be read and print a warning.
        if exists(get_index_file_name(system, index_directory)):
            try:
                f = open(index_file_name, 'r')
                record_name_list = f.read().splitlines()
                f.close()
            except Exception as e:
                print('Could not read index file for', system, str(e))
                continue

            # The channel directory will contain all the systems associated with a given channel
            for item in record_name_list:
                if item in channel_directory:
                    channel_directory[item].append(system)
                else:
                    channel_directory[item] = [system]

    return channel_directory


# -------------------------------------------------------------------------
# Cross referencing routines
# -------------------------------------------------------------------------

def system_to_others(system, database_directory, channel_dict):
    """
    Return references to records in other systems in the system's database file(s).
    It looks for record references in the field values and when it finds one
    it looks for it in the channel dictionary to determine what system it belongs to.
    The output is a list of tuples with the following information: record name,
    record field, referenced record name, referenced record field, list of systems
    where the referenced record name exists.
    :param system: system name
    :type system: str
    :param database_directory: database directory
    :type database_directory: str
    :param channel_dict: dictionary of known records
    :type channel_dict: dict
    :return: list tuples
    :rtype: list
    """
    output_list = []

    # Loop over all databases in the data directory
    for data_base_name in get_database_names(system, database_directory):

        # Open database name by file name. Open macro substitution file (if any).
        db = DatabaseFile(file_name=data_base_name)
        m = read_subs_file(data_base_name)

        # Loop over all records in the database
        for record in db.next_record():

            # Replace macros in the record name (if any)
            assert isinstance(record, EpicsRecord)
            record_name = record.get_name()
            if m is not None:
                record_name = m.replace_macros(record_name)

            # Loop over all the fields in the record. If the field value contains anything
            # matching a record name then append it to the output list, but only if it's
            # in the dictionary of known records and it belongs to a system other than the
            # one we are looking from.
            for field_name, field_value in record.get_fields():
                if m is not None:
                    field_value = m.replace_macros(field_value)
                # print field_name, field_value
                target_record_name, target_record_field = parse_field_value(field_value)
                if target_record_name is not None:
                    # print '-', record_name, record_field
                    if target_record_name in channel_dict and system not in channel_dict[target_record_name]:
                        output_list.append((target_record_name, target_record_field,
                                            # record.get_name(), field_name,
                                            record_name, field_name,
                                            channel_dict[target_record_name]))

    # return remove_duplicates(output_list)
    # print output_list
    return output_list


def others_to_system(system, sys_list, database_directory, channel_dict):
    """
    :param system: system name we are looking for
    :type system: str
    :param sys_list: list of all systems
    :type sys_list: list
    :param database_directory: database directory
    :type database_directory: str
    :param channel_dict: dictionary of known records
    :type channel_dict: dict
    :return:
    :rtype: dict
    """
    print('others_to_system')
    # Remove the system from the list of systems (we don't want references to itself)
    other_systems = sys_list
    other_systems.remove(system)
    output_dict = {}

    # Loop over all systems
    for sys_name in other_systems:
        # Loop over all databases for that system
        for data_base_name in get_database_names(sys_name, database_directory):

            # Open database by name
            db = DatabaseFile(file_name=data_base_name)
            m = read_subs_file(data_base_name)
            # print '+', data_base_name, m

            # Loop over all records in the database
            for record in db.next_record():
                assert isinstance(record, EpicsRecord)
                # Loop over all fields in the database. If the field value contains anything
                # matching a record name then add it to the output dictionary, but only if it's
                # in the dictionary of known records and it belongs to a system we are looking for.
                for field_name, field_value in record.get_fields():
                    if m is not None:
                        field_value = m.replace_macros(field_value)
                    target_record_name, target_record_field = parse_field_value(field_value)
                    if target_record_name is not None:
                        if target_record_name in channel_dict and system in channel_dict[target_record_name]:
                            # print sys_name, target_record_name, target_record_field
                            if sys_name in output_dict:
                                output_dict[sys_name].append((target_record_name, target_record_field,
                                                              record.get_name(), field_name))
                            else:
                                output_dict[sys_name] = [(target_record_name, target_record_field,
                                                          record.get_name(), field_name)]
    # print output_dict
    return output_dict


def process_system(system, sys_list, database_directory, channel_dict, include_fields):
    """
    Main cross reference routine.
    It calls the other two cross referencing routines and prints their output.
    :param system: system name
    :type system: str
    :param sys_list: system list
    :type sys_list: list
    :param database_directory: database directory
    :type database_directory: str
    :param channel_dict: channel directory
    :type channel_dict: dict
    :param include_fields:
    :type include_fields: bool
    :return: nothing
    """
    # print 'process_system', system, sys_list
    print_system_to_others(system, system_to_others(system, database_directory, channel_dict), include_fields)
    print_others_to_system(system, others_to_system(system, sys_list, database_directory, channel_dict), include_fields)
    return


# -------------------------------------------------------------------------
# Formatted output routines
# -------------------------------------------------------------------------

def print_system_to_others(system, input_list, include_fields):
    """
    :param system: system name
    :type system: str
    :param input_list: list of tuples with cross references
    :type input_list: list
    :param include_fields: include fields in output?
    :type include_fields: bool
    :return: nothing
    """
    print('-' * 80)
    print('References from ' + system + ' to ' + 'other systems:')
    if include_fields:
        for target_record, target_field, source_record, source_field, sys_list in sorted(input_list,
                                                                                         key=lambda t: t[0]):
            # print target_record, target_field, source_record, source_field, system_list
            # full_target = target_record + '.' + target_field
            sys_names = ','.join(str(x) for x in sys_list)
            print('  {0:35s} {1:35s} {2:s}'.format(target_record + '.' + target_field,
                                                   source_record + '.' + source_field,
                                                   sys_names))
    else:
        aux_list = []
        for target_record, target_field, source_record, source_field, sys_list in sorted(input_list,
                                                                                         key=lambda t: t[0]):
            # print target_record, target_field, source_record, source_field, system_list
            if target_record in aux_list:
                continue
            else:
                aux_list.append(target_record)
            sys_names = ','.join(str(x) for x in sys_list)
            print('  {0:30s} {1:s}'.format(target_record, sys_names))
    return


def print_others_to_system(system, input_dict, include_fields):
    """
    :param system:
    :type system: str
    :param input_dict:
    :type input_dict: dict
    :param include_fields: include fields in output?
    :type include_fields: bool
    :return:
    """
    print('-' * 80)
    # print input_dict
    print('References to ' + system + ' from other systems:')
    if include_fields:
        for system in sorted(input_dict):
            print(system)
            for target_record, target_field, source_record, source_field in sorted(input_dict[system]):
                print('  {0:35s}  {1:35s}'.format(target_record + '.' + target_field,
                                                  source_record + '.' + source_field))
    else:
        for system in sorted(input_dict):
            print(system)
            aux_list = []
            for target_record, target_field, source_record, source_field in sorted(input_dict[system]):
                # print target_record, aux_list
                if target_record in aux_list:
                    continue
                else:
                    aux_list.append(target_record)
                print('  {0:s}'.format(target_record))
    return


# -------------------------------------------------------------------------
# Command line parsing and main program
# -------------------------------------------------------------------------

def get_args(argv):
    """
    Process command line arguments
    :param argv: command line arguments from sys.argv
    :type argv: list
    :return: arguments
    :rtype: argparse.Namespace
    """

    parser = ArgumentParser()

    parser.add_argument(action='store',
                        nargs=1,
                        dest='system',
                        default=[],
                        help='system name')

    parser.add_argument('-d', '--data_directory',
                        action='store',
                        dest='data',
                        default=DEFAULT_DATABASE_DIRECTORY,
                        help='data directory default=(' + DEFAULT_DATABASE_DIRECTORY + ')')

    parser.add_argument('-i', '--index_directory',
                        action='store',
                        dest='indices',
                        default=DEFAULT_INDEX_DIRECTORY,
                        help='index directory default=(' + DEFAULT_INDEX_DIRECTORY + ')')

    parser.add_argument('-r', '--rebuild',
                        action='store_true',
                        dest='rebuild',
                        default=False,
                        help='rebuild index files default=(False)')

    parser.add_argument('-f', '--fields',
                        action='store_true',
                        dest='fields',
                        default=False,
                        help='show record and names default=(False)')

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    return parser.parse_args(argv[1:])


if __name__ == '__main__':

    # Process command line argument
    # args = get_args(['crossref', 'pcs', '-f'])
    # args = get_args(['crossref', 'mcs'])
    # args = get_args(['crossref', 'tcs', '-f'])
    # args = get_args(['crossref', '-h'])
    args = get_args(sys.argv)
    # print args

    # Get system name. This is the system that be cross checked.
    system_name = args.system[0]
    # print system_name

    # Get system list from the data directory and check whether the
    # system name to run a crosscheck on is in that list
    system_list = get_system_list(args.data)
    # print system_list
    if system_name not in system_list:
        print('No data for that system found')
        exit(1)

    # Read the index files for all systems in the system list.
    # The indices will be rebuilt if args.rebuild is true.
    channel_indices = build_indices(system_list, args.data, args.indices, args.rebuild)
    if channel_indices is None:
        print('No index files could be read')
        exit(1)

    # exit(0)
    # print len(channel_indices)
    # print_sorted_dictionary(channel_indices)

    # Run the crosscheck
    process_system(system_name, system_list, args.data, channel_indices, args.fields)

    exit(0)
