import os
import pytest
import filecmp
import shutil
from db import DatabaseFile, EpicsRecord

# Database file names used in this test
SINGLE_RECORD = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'db', 'single.db')
SORTED_RECORD = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'db', 'single_sorted.db')


@pytest.fixture
def epics_record():
    """
    Fixture used to return a valid EpicsRecord object from single.db
    :return: epics record
    :rtype: EpicsRecord
    """
    df = DatabaseFile(file_name=SINGLE_RECORD)
    record = None
    for record in df.next_record():
        break
    return record


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
    record = EpicsRecord('my_name', 'my_type')
    assert (record.get_name() == 'my_name')
    assert (record.get_type() == 'my_type')


def test_get_field_names_1():
    record = EpicsRecord('my_name', 'my_type')
    assert (record.get_field_names() == [])


def test_get_field_names_2(epics_record):
    assert (isinstance(epics_record, EpicsRecord))
    assert (sorted(epics_record.get_field_names()) == ['ADEL', 'AOFF', 'ASLO', 'DESC', 'DISS', 'DISV', 'DTYP', 'EGU',
                                                       'EGUF', 'EGUL', 'EVNT', 'FLNK', 'HHSV', 'HIGH', 'HIHI', 'HOPR',
                                                       'HSV', 'HYST', 'INP', 'LINR', 'LLSV', 'LOLO', 'LOPR', 'LOW',
                                                       'LSV', 'MDEL', 'PHAS', 'PINI', 'PREC', 'PRIO', 'SCAN', 'SDIS',
                                                       'SIML', 'SIMS', 'SIOL', 'SMOO'])


def test_get_field_value_1():
    record = EpicsRecord('my_name', 'my_type')
    assert (record.get_field_value('WHATEVER') is None)


def test_get_field_value_2(epics_record):
    assert (isinstance(epics_record, EpicsRecord))
    assert (epics_record.get_field_value('DESC') == 'analog input record')
    assert (epics_record.get_field_value('SCAN') == 'I/O Intr')
    assert (epics_record.get_field_value('PINI') == 'NO')
    assert (epics_record.get_field_value('PHAS') == '0')
    assert (epics_record.get_field_value('EVNT') == '0')
    assert (epics_record.get_field_value('DTYP') == 'Analog I/O')
    assert (epics_record.get_field_value('DISV') == '1')
    assert (epics_record.get_field_value('SDIS') == '0.000000000000000e+00')
    assert (epics_record.get_field_value('DISS') == 'NO_ALARM')
    assert (epics_record.get_field_value('PRIO') == 'LOW')
    assert (epics_record.get_field_value('FLNK') == '0.000000000000000e+00')
    assert (epics_record.get_field_value('INP') == '@memory')
    assert (epics_record.get_field_value('PREC') == '0')
    assert (epics_record.get_field_value('LINR') == 'LINEAR')
    assert (epics_record.get_field_value('EGUF') == '0.0000000e+00')
    assert (epics_record.get_field_value('EGUL') == '0.0000000e+00')
    assert (epics_record.get_field_value('EGU') == 'Percentage')
    assert (epics_record.get_field_value('HOPR') == '0.0')
    assert (epics_record.get_field_value('LOPR') == '0.0')
    assert (epics_record.get_field_value('AOFF') == '0.0000000e+00')
    assert (epics_record.get_field_value('ASLO') == '1.0')
    assert (epics_record.get_field_value('SMOO') == '0.0000000e+00')
    assert (epics_record.get_field_value('HIHI') == '90.0')
    assert (epics_record.get_field_value('LOLO') == '0.0')
    assert (epics_record.get_field_value('HIGH') == '60.0')
    assert (epics_record.get_field_value('LOW') == '0.0')
    assert (epics_record.get_field_value('HHSV') == 'MAJOR')
    assert (epics_record.get_field_value('LLSV') == 'NO_ALARM')
    assert (epics_record.get_field_value('HSV') == 'MINOR')
    assert (epics_record.get_field_value('LSV') == 'NO_ALARM')
    assert (epics_record.get_field_value('HYST') == '0.000000000000000e+00')
    assert (epics_record.get_field_value('ADEL') == '0.000000000000000e+00')
    assert (epics_record.get_field_value('MDEL') == '0.000000000000000e+00')
    assert (epics_record.get_field_value('SIOL') == '0.000000000000000e+00')
    assert (epics_record.get_field_value('SIML') == '0.000000000000000e+00')
    assert (epics_record.get_field_value('SIMS') == 'NO_ALARM')
    assert (epics_record.get_field_value('WHATEVER') is None)


def test_get_fields_1():
    record = EpicsRecord('my_name', 'my_type')
    assert (record.get_fields() == [])


def test_get_fields_2(epics_record):
    assert (isinstance(epics_record, EpicsRecord))
    assert (sorted(epics_record.get_fields()) == [('ADEL', '0.000000000000000e+00'), ('AOFF', '0.0000000e+00'),
                                                  ('ASLO', '1.0'), ('DESC', 'analog input record'),
                                                  ('DISS', 'NO_ALARM'), ('DISV', '1'), ('DTYP', 'Analog I/O'),
                                                  ('EGU', 'Percentage'), ('EGUF', '0.0000000e+00'),
                                                  ('EGUL', '0.0000000e+00'), ('EVNT', '0'),
                                                  ('FLNK', '0.000000000000000e+00'), ('HHSV', 'MAJOR'),
                                                  ('HIGH', '60.0'), ('HIHI', '90.0'), ('HOPR', '0.0'), ('HSV', 'MINOR'),
                                                  ('HYST', '0.000000000000000e+00'), ('INP', '@memory'),
                                                  ('LINR', 'LINEAR'), ('LLSV', 'NO_ALARM'), ('LOLO', '0.0'),
                                                  ('LOPR', '0.0'), ('LOW', '0.0'), ('LSV', 'NO_ALARM'),
                                                  ('MDEL', '0.000000000000000e+00'), ('PHAS', '0'), ('PINI', 'NO'),
                                                  ('PREC', '0'), ('PRIO', 'LOW'), ('SCAN', 'I/O Intr'),
                                                  ('SDIS', '0.000000000000000e+00'), ('SIML', '0.000000000000000e+00'),
                                                  ('SIMS', 'NO_ALARM'), ('SIOL', '0.000000000000000e+00'),
                                                  ('SMOO', '0.0000000e+00')])


def test_add_field():
    record = EpicsRecord('my_name', 'my_type')
    record.add_field('field1', 'value1')
    record.add_field('field2', 'value2')
    assert (record.get_field_names() == ['field1', 'field2'])
    assert (record.get_field_value('field1') == 'value1')
    assert (record.get_field_value('field2') == 'value2')
    assert (record.get_fields() == [('field1', 'value1'), ('field2', 'value2')])


def test_write_record(epics_record, tmp_path):
    output_file_name = os.path.join(str(tmp_path), 'output.db')
    f = open(output_file_name, 'w')
    epics_record.write_record(f_out=f)
    f.close()
    assert (filecmp.cmp(output_file_name, SINGLE_RECORD))
    shutil.rmtree(str(tmp_path), ignore_errors=True)


def test_write_sorted_record(epics_record, tmp_path):
    output_file_name = os.path.join(str(tmp_path), 'sorted.db')
    f = open(output_file_name, 'w')
    epics_record.write_sorted_record(f_out=f)
    f.close()
    assert (filecmp.cmp(output_file_name, SORTED_RECORD))
    shutil.rmtree(str(tmp_path), ignore_errors=True)


if __name__ == '__main__':
    pass
