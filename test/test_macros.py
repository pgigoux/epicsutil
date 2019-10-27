import pytest
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
    m = EpicsMacro([('top', 'ccs'), ('dev', 'motor'), ('sys', 'focus')])
    assert (m.get_macros('$(top) ${top}')) == {'top'}
    assert (m.get_macros('$(top) ${dev}')) == {'top', 'dev'}
    assert (m.get_macros('$(top) ${dev} $(sys)')) == {'top', 'dev', 'sys'}


def test_replace_macros():
    m = EpicsMacro([('top', 'ccs'), ('dev', 'motor'), ('sys', 'focus')])
    assert (m.replace_macros('top=$(top),dev=$(dev) ${sys}') == 'top=ccs,dev=motor focus')
    assert (m.replace_macros('${top}$(top)$(dev)') == 'ccsccsmotor')

