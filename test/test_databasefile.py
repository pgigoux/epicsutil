import os
import pytest
from db import DatabaseFile, EpicsDatabase, EpicsRecord


@pytest.fixture
def file_object():
    """
    Fixture used to return a valid file object
    :return: file object from open()
    """
    file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'db', 'simple.db')
    return open(file_name, 'r')


@pytest.fixture
def database_file():
    """
    Fixture used to return a valid DatabaseFile object
    :return: database file
    :rtype: DatabaseFile
    """
    file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'db', 'simple.db')
    return DatabaseFile(file_name=file_name)


def test_constructor(file_object):
    try:
        DatabaseFile()
    except FileNotFoundError:
        pass
    try:
        DatabaseFile(file_name='inexistent.db')
    except FileNotFoundError:
        pass
    DatabaseFile(file_object)
    DatabaseFile(f_in=file_object)


def test_extract_name_and_type(database_file):
    """
    Test the _extract_record_name_and_type function.
    :param database_file: database file
    :type database_file: DatabaseFile
    """
    df = database_file
    assert (df._extract_record_name_and_type('record(bi,"cs:health") {') == ('cs:health', 'bi'))
    assert (df._extract_record_name_and_type('record(bi,cs:health) {') == ('cs:health', 'bi'))
    assert (df._extract_record_name_and_type('record(bi,"") {') == (None, None))
    assert (df._extract_record_name_and_type('record(bi,) {') == (None, None))
    assert (df._extract_record_name_and_type('record(,"name") {') == (None, None))
    assert (df._extract_record_name_and_type('record(,) {') == (None, None))
    assert (df._extract_record_name_and_type('record() {') == (None, None))
    assert (df._extract_record_name_and_type('record(') == (None, None))
    assert (df._extract_record_name_and_type('field(SCAN,"I/O Intr")) {') == (None, None))
    assert (df._extract_record_name_and_type('anything else') == (None, None))


def test_record_end(database_file):
    df = database_file
    try:
        assert (df._record_end())
    except TypeError:
        pass
    assert (df._record_end('}'))
    assert (df._record_end('  }'))
    assert (df._record_end('}  '))
    assert (df._record_end('  }  '))


def test_next_record_name(database_file):
    record_name_list = [x for x in database_file.next_record_name()]
    assert (len(record_name_list) == 3)
    assert (sorted(record_name_list) == [('cs:cpuUsedPercent', 'ai'), ('cs:fdUsedPercent', 'ai'),
                                         ('cs:memoryUsedPercent', 'ai')])


def test_next_record_1(database_file):
    record_list = [x for x in database_file.next_record()]
    assert (len(record_list) == 3)


def test_next_record_2(database_file):
    for record in database_file.next_record():
        assert (isinstance(record, EpicsRecord))


def test_read_database(database_file):
    db = database_file.read_database()
    assert (type(db) == EpicsDatabase)


if __name__ == '__main__':
    pass
