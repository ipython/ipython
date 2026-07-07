"""These kinds of tests are less than ideal, but at least they run.

This was an old test that was being run interactively in the top-level tests/
directory, which we are removing.  For now putting this here ensures at least
we do run the test, though ultimately this functionality should all be tested
with better-isolated tests that don't rely on the global instance in iptest.
"""

import pytest

from IPython.core.magics.auto import AutoMagics
from IPython.core.splitinput import LineInfo
from IPython.core.prefilter import AutocallChecker


def doctest_autocall():
    """
    In [1]: def f1(a,b,c):
       ...:     return a+b+c
       ...:

    In [2]: def f2(a):
       ...:     return a + a
       ...:

    In [3]: def r(x):
       ...:     return True
       ...:

    In [4]: ;f2 a b c
    Out[4]: 'a b ca b c'

    In [5]: assert _ == "a b ca b c"

    In [6]: ,f1 a b c
    Out[6]: 'abc'

    In [7]: assert _ == 'abc'

    In [8]: print(_)
    abc

    In [9]: /f1 1,2,3
    Out[9]: 6

    In [10]: assert _ == 6

    In [11]: /f2 4
    Out[11]: 8

    In [12]: assert _ == 8

    In [12]: del f1, f2

    In [13]: ,r a
    Out[13]: True

    In [14]: assert _ == True

    In [15]: r'a'
    Out[15]: 'a'

    In [16]: assert _ == 'a'
    """


def test_autocall_should_ignore_raw_strings():
    line_info = LineInfo("r'a'")
    pm = ip.prefilter_manager
    ac = AutocallChecker(shell=pm.shell, prefilter_manager=pm, config=pm.config)
    assert ac.check(line_info) is None


@pytest.fixture
def restore_automagic():
    mman = ip.magics_manager
    saved = mman.auto_magic
    yield mman
    mman.auto_magic = saved


@pytest.fixture
def restore_autocall():
    saved = ip.autocall
    yield
    ip.autocall = saved


def test_automagic_on_off_explicit(restore_automagic, capsys):
    mman = restore_automagic
    for arg in ("on", "1", "true"):
        ip.run_line_magic("automagic", arg)
        assert mman.auto_magic is True
        out = capsys.readouterr().out
        assert "Automagic is ON, % prefix IS NOT needed for line magics." in out
    for arg in ("off", "0", "false"):
        ip.run_line_magic("automagic", arg)
        assert mman.auto_magic is False
        out = capsys.readouterr().out
        assert "Automagic is OFF, % prefix IS needed for line magics." in out


def test_automagic_case_insensitive(restore_automagic):
    mman = restore_automagic
    ip.run_line_magic("automagic", "OFF")
    assert mman.auto_magic is False
    ip.run_line_magic("automagic", "ON")
    assert mman.auto_magic is True


def test_automagic_toggle(restore_automagic):
    mman = restore_automagic
    mman.auto_magic = True
    ip.run_line_magic("automagic", "")
    assert mman.auto_magic is False
    ip.run_line_magic("automagic", "")
    assert mman.auto_magic is True


def test_autocall_set_modes(restore_autocall, capsys):
    for arg, expected, status in (("2", 2, "Full"), ("1", 1, "Smart"), ("0", 0, "Off")):
        ip.run_line_magic("autocall", arg)
        assert ip.autocall == expected
        out = capsys.readouterr().out
        assert "Automatic calling is: %s" % status in out


def test_autocall_invalid_mode(restore_autocall, caplog):
    ip.autocall = 1
    ip.run_line_magic("autocall", "3")
    # invalid mode leaves the setting unchanged and logs an error
    assert ip.autocall == 1
    assert "Valid modes: 0->Off, 1->Smart, 2->Full" in caplog.text


def test_autocall_toggle_remembers_previous_mode(restore_autocall, capsys):
    ip.run_line_magic("autocall", "2")
    assert ip.autocall == 2
    # toggling turns it off...
    ip.run_line_magic("autocall", "")
    assert ip.autocall == 0
    out = capsys.readouterr().out
    assert "Automatic calling is: Off" in out
    # ... and toggling again restores the saved mode
    ip.run_line_magic("autocall", "")
    assert ip.autocall == 2
    out = capsys.readouterr().out
    assert "Automatic calling is: Full" in out


def test_autocall_toggle_without_saved_state(restore_autocall):
    # A fresh AutoMagics instance has no saved autocall state, so toggling
    # from off defaults to smart mode (1).
    ip.autocall = 0
    am = AutoMagics(ip)
    am.autocall("")
    assert ip.autocall == 1
