from db import EpicsMacro


def test_constructor():
    try:
        EpicsMacro()
    except TypeError:
        pass
    try:
        EpicsMacro(None)
    except TypeError:
        pass
    try:
        EpicsMacro(['a', 'b', 'c'])
    except IndexError:
        pass
    EpicsMacro([('a', 'b'), ('c', 'd')])


def test_cleaned_macro():
    assert (EpicsMacro._cleaned_macro('${top}') == 'top')
    assert (EpicsMacro._cleaned_macro('$(top)') == 'top')


def test_get_macros():
    m = EpicsMacro([('top', 'cs'), ('dev', 'motor'), ('sys', 'focus')])
    assert (m.get_macros('$(top) ${top}')) == {'top'}
    assert (m.get_macros('$(top) ${dev}')) == {'top', 'dev'}
    assert (m.get_macros('$(top) ${dev} $(sys)')) == {'top', 'dev', 'sys'}


def test_replace_macros():
    m = EpicsMacro([('top', 'cs'), ('dev', 'motor'), ('sys', 'focus')])
    assert (m.replace_macros('top=$(top),dev=$(dev) ${sys}') == 'top=cs,dev=motor focus')
    assert (m.replace_macros('${top}$(top)$(dev)') == 'cscsmotor')
    try:
        assert (m.replace_macros('${top}:$(dev):$(other)', report_undefined=True) == 'cs:motor')
    except KeyError:
        pass
    assert (m.replace_macros('${top}:$(dev):$(other)', report_undefined=False) == 'cs:motor:$(other)')

    m = EpicsMacro([('top', 'cs'), ('dev', 'motor'), ('sys', 'focus')], add_undefined=True)
    assert (m.replace_macros('$(top,undefined):${dev}:$(sys):${top}') == 'cs:motor:focus:cs')
    assert (m.replace_macros('$(top,undefined):${dev,undefined}:${sys,undefined}:${top}') == 'cs:motor:focus:cs')


if __name__ == '__main__':
    pass
