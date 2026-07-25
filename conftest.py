"""pytest configuration shared by the test modules and the doctests."""

import pytest


@pytest.fixture(autouse=True)
def stop_script_magics_event_loop():
    """Shut the ``%%script`` background event loop down after every test.

    ``ScriptMagics`` starts an asyncio loop in a daemon thread the first time a
    script magic runs, and then keeps it around to be reused. The shell is
    session-scoped here, so that thread would otherwise outlive the test (or
    the doctest) that started it and leave every later test running in a
    multi-threaded process, which makes the ``os.forkpty()`` calls of, e.g.,
    ``tests/test_process.py`` emit a DeprecationWarning on Python 3.12 and
    above. The loop is recreated on demand, so stopping it is invisible to the
    tests that come after.
    """
    yield

    from IPython.terminal.interactiveshell import TerminalInteractiveShell

    shell = TerminalInteractiveShell._instance
    if shell is None:
        return
    script_magics = shell.magics_manager.registry.get("ScriptMagics")
    if script_magics is not None:
        script_magics.stop_event_loop()
