import os
import pytest
from db import DatabaseFile, EpicsDatabase, EpicsRecord

# Database file name used in this test
SIMPLE_DATABASE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'db', 'simple.db')
LARGER_DATABASE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'db', 'larger.db')


@pytest.fixture
def database_file():
    """
    Fixture used to return a valid DatabaseFile object
    :return: database file
    :rtype: DatabaseFile
    """
    return DatabaseFile(file_name=SIMPLE_DATABASE)


@pytest.fixture
def epics_database():
    df = DatabaseFile(file_name=SIMPLE_DATABASE)
    db = EpicsDatabase()
    for record in df.next_record():
        db.add_record(record)
    return db


@pytest.fixture
def larger_epics_database():
    df = DatabaseFile(file_name=LARGER_DATABASE)
    db = EpicsDatabase()
    for record in df.next_record():
        db.add_record(record)
    return db


def test_constructor():
    try:
        EpicsDatabase('something')
    except TypeError:
        pass
    EpicsDatabase()


def test_add_record(database_file):
    """
    :param database_file: database file object
    :type database_file: DatabaseFile
    :return:
    """
    assert (isinstance(database_file, DatabaseFile))
    db = EpicsDatabase()
    for record in database_file.next_record():
        db.add_record(record)


def test_get_record_names(epics_database):
    """
    :param epics_database: epics database object
    :type epics_database: EpicsDatabase
    """
    assert (isinstance(epics_database, EpicsDatabase))
    assert (sorted(epics_database.get_record_names()) == ['cs:cpuUsedPercent', 'cs:fdUsedPercent',
                                                          'cs:memoryUsedPercent'])


def test_get_record(epics_database):
    """
    :param epics_database: epics database object
    :type epics_database: EpicsDatabase
    """
    assert (isinstance(epics_database, EpicsDatabase))
    for record_name in epics_database.get_record_names():
        assert (isinstance(epics_database.get_record(record_name), EpicsRecord))


def test_record_count(epics_database):
    assert (isinstance(epics_database, EpicsDatabase))
    assert (epics_database.record_count() == 3)


def test_append_1(epics_database, larger_epics_database):
    """
    :param epics_database: epics database object
    :type epics_database: EpicsDatabase
    :param larger_epics_database: epics database object (larger database)
    :type larger_epics_database: EpicsDatabase
    """
    assert (isinstance(epics_database, EpicsDatabase))
    assert (isinstance(larger_epics_database, EpicsDatabase))
    n1 = epics_database.record_count()
    n2 = larger_epics_database.record_count()
    epics_database.append(larger_epics_database)
    assert (epics_database.record_count() == n1 + n2)


def test_append_2(epics_database, larger_epics_database):
    """
    :param epics_database: epics database object
    :type epics_database: EpicsDatabase
    :param larger_epics_database: epics database object (larger database)
    :type larger_epics_database: EpicsDatabase
    """
    assert (isinstance(epics_database, EpicsDatabase))
    epics_database.append(larger_epics_database)
    assert (sorted(epics_database.get_record_names()) == ['ccs:instCvr:close', 'ccs:instCvr:closeBo',
                                                          'ccs:instCvr:closeDmd', 'ccs:instCvr:demand',
                                                          'ccs:instCvr:f1', 'ccs:instCvr:open',
                                                          'ccs:instCvr:openBo', 'ccs:instCvr:openDmd',
                                                          'cs:cpuUsedPercent', 'cs:fdUsedPercent',
                                                          'cs:memoryUsedPercent'])


def test_append_3(epics_database):
    """
    :param epics_database: epics database object
    :type epics_database: EpicsDatabase
    """
    assert (isinstance(epics_database, EpicsDatabase))
    epics_database.append(epics_database)
    assert (epics_database.record_count() == 3)


if __name__ == '__main__':
    pass
