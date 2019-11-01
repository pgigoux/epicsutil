import os
import sys
import pytest
from db import DatabaseFile, EpicsDatabase, EpicsRecord


@pytest.fixture
def simple_database():
    file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'simple.db')
    return DatabaseFile(file_name=file_name)


def test_constructor():
    try:
        DatabaseFile()
    except FileNotFoundError:
        pass
    try:
        DatabaseFile(file_name='inexistent.db')
    except FileNotFoundError:
        pass
    try:
        DatabaseFile(f_in=sys.stdin)
    except FileNotFoundError:
        pass


def test_extract_name_and_type(simple_database):
    df = simple_database
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


def test_record_end(simple_database):
    df = simple_database
    try:
        assert (df._record_end())
    except TypeError:
        pass
    assert (df._record_end('}'))
    assert (df._record_end('  }'))
    assert (df._record_end('}  '))
    assert (df._record_end('  }  '))


def test_next_record_name(simple_database):
    record_name_list = [x for x in simple_database.next_record_name()]
    assert (len(record_name_list) == 3)
    assert (sorted(record_name_list) == [('cs:cpuUsedPercent', 'ai'), ('cs:fdUsedPercent', 'ai'),
                                         ('cs:memoryUsedPercent', 'ai')])


def test_next_record_1(simple_database):
    record_list = [x for x in simple_database.next_record()]
    assert (len(record_list) == 3)


def test_next_record_2(simple_database):
    for record in simple_database.next_record():
        assert (type(record) == EpicsRecord)


def test_read_database(simple_database):
    db = simple_database.read_database()
    assert (type(db) == EpicsDatabase)
