from db import DatabaseFile


def test_constructor():
    try:
        DatabaseFile()
    except FileNotFoundError:
        pass
    try:
        DatabaseFile(file_name='idonotexist.db')
    except FileNotFoundError:
        pass


def test_extract_name_and_type():
    df = DatabaseFile(file_name='simple.db')
    assert (df._extract_record_name_and_type('record(bi,"cs:health") {') == ('cs:health', 'bi'))
    assert (df._extract_record_name_and_type('record(bi,"") {') == (None, None))
    assert (df._extract_record_name_and_type('record(bi,) {') == (None, None))
    assert (df._extract_record_name_and_type('record(,"name") {') == (None, None))
    assert (df._extract_record_name_and_type('record(,) {') == (None, None))
    assert (df._extract_record_name_and_type('record() {') == (None, None))
    assert (df._extract_record_name_and_type('record(') == (None, None))
    assert (df._extract_record_name_and_type('field(SCAN,"I/O Intr")) {') == (None, None))
    assert (df._extract_record_name_and_type('anything else') == (None, None))


if __name__ == '__main__':
    pass
