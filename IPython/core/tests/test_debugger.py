"""Tests for debugging machinery.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import signal
import sys
import time
import warnings
from tempfile import NamedTemporaryFile
from subprocess import check_output, CalledProcessError, PIPE
import subprocess

import nose.tools as nt

from IPython.core import debugger

#-----------------------------------------------------------------------------
# Helper classes, from CPython's Pdb test suite
#-----------------------------------------------------------------------------

class _FakeInput(object):
    """
    A fake input stream for pdb's interactive debugger.  Whenever a
    line is read, print it (to simulate the user typing it), and then
    return it.  The set of lines to return is specified in the
    constructor; they should not have trailing newlines.
    """
    def __init__(self, lines):
        self.lines = iter(lines)

    def readline(self):
        line = next(self.lines)
        print(line)
        return line+'\n'

class PdbTestInput(object):
    """Context manager that makes testing Pdb in doctests easier."""

    def __init__(self, input):
        self.input = input

    def __enter__(self):
        self.real_stdin = sys.stdin
        sys.stdin = _FakeInput(self.input)

    def __exit__(self, *exc):
        sys.stdin = self.real_stdin

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

def test_longer_repr():
    from reprlib import repr as trepr
    
    a = '1234567890'* 7
    ar = "'1234567890123456789012345678901234567890123456789012345678901234567890'"
    a_trunc = "'123456789012...8901234567890'"
    nt.assert_equal(trepr(a), a_trunc)
    # The creation of our tracer modifies the repr module's repr function
    # in-place, since that global is used directly by the stdlib's pdb module.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        debugger.Tracer()
    nt.assert_equal(trepr(a), ar)

def test_ipdb_magics():
    '''Test calling some IPython magics from ipdb.

    First, set up some test functions and classes which we can inspect.

    >>> class ExampleClass(object):
    ...    """Docstring for ExampleClass."""
    ...    def __init__(self):
    ...        """Docstring for ExampleClass.__init__"""
    ...        pass
    ...    def __str__(self):
    ...        return "ExampleClass()"

    >>> def example_function(x, y, z="hello"):
    ...     """Docstring for example_function."""
    ...     pass

    >>> old_trace = sys.gettrace()

    Create a function which triggers ipdb.

    >>> def trigger_ipdb():
    ...    a = ExampleClass()
    ...    debugger.Pdb().set_trace()

    >>> with PdbTestInput([
    ...    'pdef example_function',
    ...    'pdoc ExampleClass',
    ...    'up',
    ...    'down',
    ...    'list',
    ...    'pinfo a',
    ...    'll',
    ...    'continue',
    ... ]):
    ...     trigger_ipdb()
    --Return--
    None
    > <doctest ...>(3)trigger_ipdb()
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> pdef example_function
     example_function(x, y, z='hello')
     ipdb> pdoc ExampleClass
    Class docstring:
        Docstring for ExampleClass.
    Init docstring:
        Docstring for ExampleClass.__init__
    ipdb> up
    > <doctest ...>(11)<module>()
          7    'pinfo a',
          8    'll',
          9    'continue',
         10 ]):
    ---> 11     trigger_ipdb()
    <BLANKLINE>
    ipdb> down
    None
    > <doctest ...>(3)trigger_ipdb()
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> list
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> pinfo a
    Type:           ExampleClass
    String form:    ExampleClass()
    Namespace:      Local...
    Docstring:      Docstring for ExampleClass.
    Init docstring: Docstring for ExampleClass.__init__
    ipdb> ll
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> continue
    
    Restore previous trace function, e.g. for coverage.py    
    
    >>> sys.settrace(old_trace)
    '''

def test_ipdb_magics2():
    '''Test ipdb with a very short function.
    
    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    Run ipdb.

    >>> with PdbTestInput([
    ...    'continue',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
          1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> continue
    
    Restore previous trace function, e.g. for coverage.py    
    
    >>> sys.settrace(old_trace)
    '''

def can_quit():
    '''Test that quit work in ipydb

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    >>> with PdbTestInput([
    ...    'quit',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
            1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> quit

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    '''


def can_exit():
    '''Test that quit work in ipydb

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    >>> with PdbTestInput([
    ...    'exit',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
            1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> exit

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    '''


interruptible_debugger = """\
import sys
import threading
import time
from os import _exit
from bdb import BdbQuit

from IPython.core.debugger import set_trace

# Timeout if the interrupt doesn't happen:
def timeout():
    time.sleep(5)
    _exit(7)
threading.Thread(target=timeout, daemon=True).start()

def break_handler(*args):
    print("BREAK!")
    raise KeyboardInterrupt()

def main():
    import signal
    signal.signal(signal.SIGBREAK, break_handler)
    set_trace()

if __name__ == '__main__':
    try:
        print("Starting debugger...")
        main()
        print("Debugger exited without error.")
    except (KeyboardInterrupt, BdbQuit):
        print("Caught KeyboardInterrupt or BdbQuit, PASSED")
    except Exception as e:
        print("Got wrong exception...")
        raise e
"""


def test_interruptible_core_debugger():
    """The debugger can be interrupted.
    
    See https://stackoverflow.com/a/35792192 for details on Windows.
    """
    with NamedTemporaryFile("w", delete=False) as f:
        f.write(interruptible_debugger)
        f.flush()
    start = time.time()
    
    p = subprocess.Popen([sys.executable, "-u", f.name],
                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, # TODO disable on posix
                         encoding=sys.getdefaultencoding(),
                         stderr=PIPE, stdout=PIPE)
    time.sleep(1)  # wait for it to hit pdb
    if sys.platform == "win32":
        # Yes, this has to happen once. I have no idea why.
        p.send_signal(signal.CTRL_BREAK_EVENT)
        p.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        p.send_signal(signal.SIGINT)
    exit_code = p.wait()
    stdout = p.stdout.read()
    stderr = p.stderr.read()
    print("STDOUT", stdout, file=sys.__stderr__)
    print("STDERR", stderr, file=sys.__stderr__)
    assert exit_code == 0
    print("SUCCESS!", file=sys.__stderr__)
    # Make sure it exited cleanly, and quickly:
    end = time.time()
    assert end - start < 2  # timeout is 5 seconds
    assert "PASSED" in stdout