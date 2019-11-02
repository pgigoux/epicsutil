import os
import pytest
from db import DatabaseFile, EpicsRecord


@pytest.fixture
def database_file():
    """
    Fixture used to return a valid DatabaseFile object
    :return: database file
    :rtype: DatabaseFile
    """
    file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'db', 'single.db')
    return DatabaseFile(file_name=file_name)


def test_constructor():
    try:
        EpicsRecord()
    except TypeError:
        pass
    try:
        EpicsRecord('name')
    except TypeError:
        pass
    try:
        EpicsRecord('name', 3)
    except TypeError:
        pass
    try:
        EpicsRecord(2.0, 'type')
    except TypeError:
        pass
    try:
        EpicsRecord(None, None)
    except TypeError:
        pass
    EpicsRecord('name', 'type')


def test_get_name_and_type():
    record = EpicsRecord('name', 'type')
    assert (record.get_name() == 'name')
    assert (record.get_type() == 'type')


def test_get_field_names(database_file):
    for record in database_file.next_record():
        break
    assert (isinstance(record, EpicsRecord))
    assert (sorted(record.get_field_names()) == ['ADEL', 'AOFF', 'ASLO', 'DESC', 'DISS', 'DISV', 'DTYP', 'EGU',
                                                 'EGUF', 'EGUL', 'EVNT', 'FLNK', 'HHSV', 'HIGH', 'HIHI', 'HOPR',
                                                 'HSV', 'HYST', 'INP', 'LINR', 'LLSV', 'LOLO', 'LOPR', 'LOW',
                                                 'LSV', 'MDEL', 'PHAS','PINI', 'PREC', 'PRIO', 'SCAN', 'SDIS',
                                                 'SIML', 'SIMS', 'SIOL', 'SMOO'])


def test_get_field_value(database_file):
    for record in database_file.next_record():
        break
    assert (isinstance(record, EpicsRecord))
    assert (record.get_field_value('DESC') == 'analog input record')
    assert (record.get_field_value('SCAN') == 'I/O Intr')
    assert (record.get_field_value('PINI') == 'NO')
    assert (record.get_field_value('PHAS') == '0')
    assert (record.get_field_value('EVNT') == '0')
    assert (record.get_field_value('DTYP') ==  'Analog I/O')
    assert (record.get_field_value('DISV') == '1')
    assert (record.get_field_value('SDIS') == '0.000000000000000e+00')
    assert (record.get_field_value('DISS') == 'NO_ALARM')
    assert (record.get_field_value('PRIO') == 'LOW')
    assert (record.get_field_value('FLNK') == '0.000000000000000e+00')
    assert (record.get_field_value('INP') == '@memory')
    assert (record.get_field_value('PREC') == '0')
    assert (record.get_field_value('LINR') == 'LINEAR')
    assert (record.get_field_value('EGUF') == '0.0000000e+00')
    assert (record.get_field_value('EGUL') == '0.0000000e+00')
    assert (record.get_field_value('EGU') == 'Percentage')
    assert (record.get_field_value('HOPR') == '0.0')
    assert (record.get_field_value('LOPR') == '0.0')
    assert (record.get_field_value('AOFF') == '0.0000000e+00')
    assert (record.get_field_value('ASLO') == '1.0')
    assert (record.get_field_value('SMOO') == '0.0000000e+00')
    assert (record.get_field_value('HIHI') == '90.0')
    assert (record.get_field_value('LOLO') == '0.0')
    assert (record.get_field_value('HIGH') == '60.0')
    assert (record.get_field_value('LOW') =='0.0')
    assert (record.get_field_value('HHSV') =='MAJOR')
    assert (record.get_field_value('LLSV') == 'NO_ALARM')
    assert (record.get_field_value('HSV') == 'MINOR')
    assert (record.get_field_value('LSV') == 'NO_ALARM')
    assert (record.get_field_value('HYST') == '0.000000000000000e+00')
    assert (record.get_field_value('ADEL') == '0.000000000000000e+00')
    assert (record.get_field_value('MDEL') == '0.000000000000000e+00')
    assert (record.get_field_value('SIOL') == '0.000000000000000e+00')
    assert (record.get_field_value('SIML') == '0.000000000000000e+00')
    assert (record.get_field_value('SIMS') == 'NO_ALARM')
