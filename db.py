"""
This module defines the following classes:

1. EpicsRecord:

This class that takes care of storing an EPICS record into memory. It provides routines
to operate over the record name, type and fields. It also includes the routines to print a
an EPICS record to the standard output (sorted or unsorted fields).

2. EpicsDatabase:

This class takes care of storing a collection of EpicsRecords into memory. It provides routines
to operates on the records in the database. It does not provide routines to retrieve records
sequentially in the same order as in the database file, but includes routines to print the database
to the standard output (sorted or unsorted records and fields).

3. DatabaseFile:

It provides the routines to parse an EPICS database from disk (or standard input). The main
advantage of using DatabaseFile over EpicsDatabase is that the first one only needs to store one
record in memory at a time, and that it can read records in the same order as in the file.
There are three main routines that can be called from an application program:

  * next_record: returns the next EpicsRecord in the file.

  * next_record_name: returns the next EPICS record name and type. It is intended for programs like
    dbl that don't need the record structure.

  * read_database: Read the whole database into an EpicsDatabase object.

Field names and values and stored as tuples (there's no RecordField class).
"""
import sys
import re
from io import IOBase

# Values passed to tell the user defined filter routine what part of a record is being processed
FILTER_RECORD = 1
FILTER_FIELD = 2


def format_record_start(record_name, record_type):
    """
    Format a record name and type in the same as they appear in a valid database file
    :param record_name: record name
    :type record_name: str
    :param record_type:  record type
    :type record_type: str
    :return: record start formatted as string
    :rtype: str
    """
    return 'record({0:s},\"{1:s}\")'.format(record_type, record_name) + ' {'


def format_record_end():
    """
    Format the record end line ('}'). This routine is provided to remove output
    specific formatting from other routines.
    :return: record end formatted as string
    :rtype: str
    """
    return '}'


def format_field(name, value):
    """
    Format a field name and values in the same as they appear in a valid database file
    :param name: field name
    :type name: str
    :param value: field value
    :type value: str
    :return: field formatted as string
    :rtype: str
    """
    return '    field({0:s},"{1:s}")'.format(name, value)


class DatabaseFile:
    """
    This class is used to provide the functions needed to read an EPICS database file from disk.
    Record are stored in a dictionary indexed by the record name (order is not preserved).
    Record names are stored in a separate list that preserves the order in the file.
    The record and field filters are provided to allow application programs to edit the record
    name and type, and the field name and value. Programs like dbdiff need to do this when comparing
    databases generated by capfast and tdct.
    Note: the routines in this class do a best effort to read records from the database file and
    do not check for a valid database syntax.
    """

    # States used in the next_record() state machine
    # STATE_START: starting state, nothing has been found yet
    # STATE_RECORD: found the record start, proceed to process fields
    STATE_START = 0
    STATE_RECORD = 1

    def __init__(self, f_in=None, file_name=None, filter_function=None):
        """
        Class creator
        :param f_in: input file
        :type f_in: file
        :param file_name: input file name (used in error messages)
        :type file_name: str
        :param filter_function: function used to filter record names and fields
        :type filter_function: func
        """
        if isinstance(f_in, IOBase):
            self.f = f_in
        else:
            self.f = open(str(file_name), 'r')
        self.file_name = file_name
        self.filter = filter_function

    def __str__(self):
        """
        Return the string representation of the database file object
        :return: string representation
        :rtype: str
        """
        return '<Database file f=' + str(self.f) + ', file_name=' + str(self.file_name) + '>'

    def close(self):
        """
        Close database file. Errors are ignored.
        """
        try:
            self.f.close()
        except Exception as e:
            print(e)

    def _extract_record_name_and_type(self, line):
        """
        Extract the record name and type from a database file line (if present).
        Several pattern matching strings were used to take into account databases
        generated by capfast and VDCT, as well as those containing macro definitions.
        :param line: line from database file
        :type line: str
        :return: tuple with the record name and type if present. (None, None) otherwise.
        :rtype: tuple
        """
        if re.search(r'^\s*record.*\(', line):
            # print '--', line

            # Get rid of the 'record'keyword and the parenthesis.
            rest_of_the_line = re.sub(r'\s*record.*?\(', '', line)
            try:
                record_type, record_name = rest_of_the_line.split(',')
            except ValueError:
                return None, None
            # print('t=' + record_type, 'n=' + record_name)

            # Get rid of the everything after the the trailing parenthesis. Remove double quotes as well.
            # We cannot use regular expressions here because the record name can have macros.
            pos = record_name.rfind(')')
            if pos > 0:
                record_name = record_name[0:pos]
            else:
                return None, None  # missing record name

            # Finally, get rid of any double quotes and leading or trailing blanks
            record_type = re.sub('"', '', record_type).strip()
            if not record_type:
                return None, None  # missing record type
            record_name = re.sub('"', '', record_name).strip()
            if not record_name:
                return None, None  # missing record name

            # If defined, call the record filtering routine.
            # Otherwise trim whitespaces from the record name and type.
            if self.filter is not None:
                return self.filter(FILTER_RECORD, record_name, record_type)
            else:
                return record_name, record_type
        else:
            return None, None  # line does not contain a record definition

    def _extract_field_name_and_value(self, line):
        """
        Extract a field name and value from a line coming from a database file (if present).
        :param line: line from database file
        :type line: str
        :return: tuple containing the field name and value if present. (None, None) otherwise
        :rtype: tuple
        """
        if re.search(r'^\s*field.*\(', line):
            # print '-', line
            name, value = line.split(',', 1)
            name = re.sub(r'\s*field.*\(', '', name)
            value = re.sub(r'\)$', '', value)
            value = re.sub('"', '', value)
            # return name.strip(), value.strip()
            # print '[' + name + '] [' + value + ']'

            # If defined, call the field filtering routine.
            # Otherwise trim whitespaces from the field name only.
            if self.filter is not None:
                return self.filter(FILTER_FIELD, name, value)
            else:
                return name.strip(), value
        else:
            return None, None  # line does not contain a field definition

    @staticmethod
    def _record_end(line):
        """
        Check whether a line contains the end of a record (})
        :param line: input line
        :type line: str
        :return: True if it does, False otherwise
        :rtype: bool
        """
        if line.strip() == '}':
            return True
        else:
            return False

    def next_record_name(self):
        """
        Read the next record from the database file and return its name and type.
        The record is not stored anywhere.
        This function is intended for programs that do not care about the record fields (e.g. dbl).
        It is implemented as Python generator to allow using it in loops.
        :return: tuple with record name and type
        :rtype: tuple
        """
        for line in self.f:
            line = line.rstrip('\n')
            # print '--', line
            record_name, record_type = self._extract_record_name_and_type(line)
            # print '++', record_name, record_type
            if record_name and record_type:
                yield record_name, record_type

    def next_record(self):
        """
        Read the next record from the database file.
        Records are returned in the same order as they appear in the file.
        It will ignore lines in the file that do not match a record or field declaration.
        This routine is implemented as a Python generator to allow using it in loops.
        Note that this routine is not a full database parser so it could fail miserably
        if the database has syntax errors (e.g. a record with the missing '}' at the end).
        :return: next record
        :rtype: list
        """
        record = None
        state = self.STATE_START

        for line in self.f:
            line = line.rstrip()
            # print '--', line

            if state == self.STATE_START:
                # If the line is a record start then create a new EpicsRecord for it
                # and move to the STATE_RECORD state.
                record_name, record_type = self._extract_record_name_and_type(line)
                # print '++', record_name, record_type
                if record_name and record_type:
                    # print record_name, record_type
                    state = self.STATE_RECORD
                    record = EpicsRecord(record_name, record_type)  # create record object

            elif state == self.STATE_RECORD:
                # If the line contains a field definition then add the field name and value
                # to the current record.
                field_name, field_value = self._extract_field_name_and_value(line)
                if field_name and field_value:
                    # print field_name, field_value
                    record.add_field(field_name, field_value)  # found a field declaration
                elif self._record_end(line):
                    state = self.STATE_START
                    yield record
                else:
                    pass  # unknown line, ignore

    def read_database(self):
        """
        Read the entire database file into memory.
        The file contents is stored as an EpicsDatabase object.
        :return: database
        :rtype: EpicsDatabase
        """
        database = EpicsDatabase()
        for record in self.next_record():
            database.add_record(record)
        return database


class EpicsDatabase:
    """
    This class provides the routines to handle a database in memory
    """

    def __init__(self):
        self.records = {}
        self.record_names = []

    def add_record(self, record):
        """
        Add record to the database.
        :param record: record to add
        :type record: EpicsRecord
        """
        record_name = record.get_name()
        self.record_names.append(record_name)
        self.records[record_name] = record

    def append(self, db):
        """
        Add a database at the end of the current database.
        The records from the database being appended will overwrite the records in
        the current database if there are records with the same name.
        The order of the records will be the records from the first database followed
        by the records from the second database.
        :param db: EPICS database
        :type db: EpicsDatabase
        """
        self.records.update(db.records)
        # there's a probably a better way to do merge the names
        for record_name in db.record_names:
            if record_name not in self.record_names:
                self.record_names.append(record_name)

    def get_record_names(self):
        """
        Return the list of record names in the database
        :return: list of names
        :rtype: list
        """
        return self.record_names

    def get_record(self, record_name):
        """
        Return the record matching a record name.
        :param record_name: record name
        :type record_name: EpicsRecord
        :return: record, or None if the record is not in the database
        :rtype: EpicsRecord
        """
        if record_name in self.records.keys():
            return self.records[record_name]
        else:
            return None

    def record_count(self):
        """
        Return the number of records in the database
        :return: number of records
        :rtype: int
        """
        return len(self.records.keys())

    def write_database(self, f_out=sys.stdout):
        """
        Print the database in the same format as in the database file.
        The file is not closed to allow writing (appending) databases to a single file.
        The order of the records is preserved.
        :param f_out: output file object
        :type f_out: file
        """
        for record_name in self.record_names:
            self.records[record_name].write_record(f_out=f_out)

    def write_sorted_database(self, reverse=False, f_out=sys.stdout):
        """
        Print the database sorted by record name. It also sorts the fields in each record.
        The file is not closed to allow writing (appending) databases to a single file.
        The sorting order can be specified.
        :param reverse: reverse sort order?
        :type reverse: bool
        :param f_out: output file object
        :type f_out: file
        """
        for record_name in sorted(self.record_names, reverse=reverse):
            self.get_record(record_name).write_sorted_record(reverse=reverse, f_out=f_out)


class EpicsRecord:
    """
    This class provides the routine to handle records in memory.
    """

    def __init__(self, record_name, record_type):
        """
        :param record_name: record name
        :type record_name: str
        :param record_type: record type
        :type record_type: str
        """
        if isinstance(record_name, str) and isinstance(record_type, str):
            self.name = record_name
            self.type = record_type
        else:
            raise TypeError('the record name and type must be strings')
        self.field_names = []
        self.field_values = {}

    def get_name(self):
        """
        Return record type
        :return: record type
        :rtype: str
        """
        return self.name

    def get_type(self):
        """
        Return record type as it appears in the database file
        :return: record type
        :rtype: str
        """
        return self.type

    def get_field_names(self):
        """
        Return the list of fields for the record
        :return: list of fields
        :rtype: list
        """
        return self.field_names

    def get_field_value(self, field_name):
        """
        Return the field value for a given field name.
        It will return None if the field is not present.
        :param field_name: field name
        :type field_name: string
        :return: field value, or None if the field is not present
        :rtype: str
        """
        if field_name in self.field_values.keys():
            return self.field_values[field_name]
        else:
            return None

    def get_fields(self):
        """
        Return the fields for a record as a list of (field name, field type) tuples.
        :return: fields
        :rtype: list
        """
        return [(field_name, self.field_values[field_name]) for field_name in self.field_names]

    def add_field(self, field_name, field_value):
        """
        Add field to the record
        :param field_name: field name
        :type field_name: string
        :param field_value: field value
        :type field_value: string
        """
        self.field_names.append(field_name)
        self.field_values[field_name] = field_value

    def write_record(self, f_out=sys.stdout):
        """
        Print record in the same format as it would appear in the file.
        The file is not closed to allow writing more than one record to the same file.
        The order of the fields is preserved.
        :param f_out: output file object
        :type f_out: file
        """
        f_out.write(format_record_start(self.name, self.type) + '\n')
        for field_name in self.field_names:
            f_out.write(format_field(field_name, self.field_values[field_name]) + '\n')
        f_out.write(format_record_end() + '\n')

    def write_sorted_record(self, reverse=False, f_out=sys.stdout):
        """
        Print sorted record. The fields are sorted by name.
        The file is not closed to allow writing more than one record to the same file.
        The sort order can be specified.
        :param reverse: reverse sort order?
        :type reverse: bool
        :param f_out: output file object
        :type f_out: file
        """
        f_out.write(format_record_start(self.name, self.type) + '\n')
        for field_name in sorted(self.field_names, reverse=reverse):
            f_out.write(format_field(field_name, self.field_values[field_name]) + '\n')
        f_out.write(format_record_end() + '\n')


class EpicsMacro:
    # Regular expression used to match a record reference.
    # It's not as general as should be, but's good enough for what we want.
    # The comma is allowed in macro names to cope with the syntax
    # $(name,undefined) when macros are undefined.
    MACRO_SEARCH_REGEXP = r'\$\([a-zA-Z0-9_,]+\)|\$\{[a-zA-Z0-9_,]+\}'

    UNDEFINED_SUFFIX = ',undefined'

    def __init__(self, macro_list, add_undefined=False):
        """
        :param macro_list: list of (macro, value) tuples
        :type macro_list: list
        :param add_undefined: add "UNDEFINDED_SUFFIX" entries to the dictionary?
        :type add_undefined: bool
        """
        self.pattern = re.compile(self.MACRO_SEARCH_REGEXP)
        self.macro_dictionary = {}
        for t in macro_list:
            # print(t)
            self.macro_dictionary[t[0]] = t[1]
            if add_undefined:
                self.macro_dictionary[t[0] + self.UNDEFINED_SUFFIX] = t[1]
        # print self.macro_dictionary

    def __str__(self):
        return str(self.macro_dictionary)

    @staticmethod
    def _cleaned_macro(macro):
        """
        Extract macro name from a macro reference.
        It strips the dollar sign and the parentheses from the definition.
        :param macro: macro definition (e.g. $(top))
        :type macro: str
        :return: macro name (e.g. top)
        :rtype: str
        """
        return re.sub('[$(){}]', '', macro)

    def get_macros(self, line):
        """
        Get macros found in a line with dollar signs or parenthesis removed.
        Duplicate entries are removed.
        :param line: input line
        :type line: str
        :return: set of macros
        :rtype: set
        """
        match_list = self.pattern.finditer(line)
        return set([self._cleaned_macro(m.group()) for m in match_list])

    def replace_macros(self, line, report_undefined=True):
        """
        Replace macros in a line.
        :param line: line to replace macros
        :type line: str
        :param report_undefined: report undefined macros?
        :type report_undefined: bool
        :return:
        """
        # print('line: ' + line)
        # Look for matches only if there are macros in the dictionary
        if self.macro_dictionary:
            match_list = self.pattern.finditer(line)
            for match in match_list:
                # print('group: ' + match.group(), match.start(), match.end())
                # Extract macro name
                macro_name = self._cleaned_macro(match.group())
                # print('macro_name: ' + macro_name)

                # Replace macro with value from the dictionary
                if macro_name in self.macro_dictionary:
                    pattern = r'\$\(' + macro_name + r'\)|' + r'\$\{' + macro_name + r'\}'
                    line = re.sub(pattern, self.macro_dictionary[macro_name], line)
                elif report_undefined:
                    raise KeyError('Undefined macro [' + macro_name + ']')

        return line


def test_filter(what, name, attribute):
    """
    Test filter routine
    :param what: FILTER_RECORD or FILTER_FIELD
    :type what: int
    :param name: record name or field name
    :type name: str
    :param attribute: record type or field value
    :type attribute: str
    """
    if what == FILTER_RECORD:
        # print 'filter record', name, attribute
        value = name.replace(EpicsMacro.UNDEFINED_SUFFIX, '')
        return name.strip(), value
    else:
        value = attribute.replace(EpicsMacro.UNDEFINED_SUFFIX, '')
        return name.strip(), value.strip()
    pass


if __name__ == '__main__':
    # m = EpicsMacro([('top', 'tcs'), ('dev', 'motor')], add_undefined=True)
    # print(m.replace_macros('This is the $(top,undefined) and ${top}'))
    # print(m.macro_dictionary)
    # # print(m)
    #
    # exit(0)
    #
    # df1 = DatabaseFile(file_name='db_data/larger.db')
    # df2 = DatabaseFile(file_name='db_data/append2.db')
    # db1 = df1.read_database()
    # db2 = df2.read_database()
    # db1.append(db2)
    # f = open('junk.db', 'w')
    # db1.write_database(f_out=f)
    # f.close()
    # exit(1)
    #
    # f_test = open('test_data/crtop_rtems.db', 'r')
    #
    # df = DatabaseFile(f_test, filter_function=test_filter)
    #
    # for r in df.next_record():
    #     assert (isinstance(r, EpicsRecord))
    #     print('--- [' + r.get_name() + '] [' + r.get_type() + ']')
    #     # print r.get_fields()
    #     r.write_record()
    #
    # # df = DatabaseFile(file_name='data/diff1.db')
    #
    # df.close()
    # exit(0)
    #
    # db3 = df.read_database()
    #
    # # f = open('out4.db', 'w')
    # f = sys.stdout
    # db3.write_database(f_out=f)
    # # db.write_sorted_database(f=f)
    # # f.close()
    # # db.write_sorted_database(reverse=True)
    # exit(0)
    #
    # # for r in df.next_record():
    # #     db.add_record(r)
    # #
    # # db.print_database()
    # # print '-----------------------------------------------------------'
    # # db.write_sorted_database(reverse=True)

    exit(0)
