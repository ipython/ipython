# encoding: utf-8
"""
Tests for platutils.py
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
from unittest import TestCase

import nose.tools as nt

from IPython.utils.process import (find_cmd, FindCmdError, arg_split,
                                   system, getoutput, getoutputerror)
from IPython.testing import decorators as dec
from IPython.testing import tools as tt

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

def test_find_cmd_python():
    """Make sure we find sys.exectable for python."""
    nt.assert_equals(find_cmd('python'), sys.executable)

    
@dec.skip_win32
def test_find_cmd_ls():
    """Make sure we can find the full path to ls."""
    path = find_cmd('ls')
    nt.assert_true(path.endswith('ls'))

    
def has_pywin32():
    try:
        import win32api
    except ImportError:
        return False
    return True


@dec.onlyif(has_pywin32, "This test requires win32api to run")
def test_find_cmd_pythonw():
    """Try to find pythonw on Windows."""
    path = find_cmd('pythonw')
    nt.assert_true(path.endswith('pythonw.exe'))


@dec.onlyif(lambda : sys.platform != 'win32' or has_pywin32(),
            "This test runs on posix or in win32 with win32api installed")
def test_find_cmd_fail():
    """Make sure that FindCmdError is raised if we can't find the cmd."""
    nt.assert_raises(FindCmdError,find_cmd,'asdfasdf')

    
@dec.skip_win32
def test_arg_split():
    """Ensure that argument lines are correctly split like in a shell."""
    tests = [['hi', ['hi']],
             [u'hi', [u'hi']],
             ['hello there', ['hello', 'there']],
             # \u01ce == \N{LATIN SMALL LETTER A WITH CARON}
             # Do not use \N because the tests crash with syntax error in
             # some cases, for example windows python2.6.
             [u'h\u01cello', [u'h\u01cello']],
             ['something "with quotes"', ['something', '"with quotes"']],
             ]
    for argstr, argv in tests:
        nt.assert_equal(arg_split(argstr), argv)
    
@dec.skip_if_not_win32
def test_arg_split_win32():
    """Ensure that argument lines are correctly split like in a shell."""
    tests = [['hi', ['hi']],
             [u'hi', [u'hi']],
             ['hello there', ['hello', 'there']],
             [u'h\u01cello', [u'h\u01cello']],
             ['something "with quotes"', ['something', 'with quotes']],
             ]
    for argstr, argv in tests:
        nt.assert_equal(arg_split(argstr), argv)


class SubProcessTestCase(TestCase, tt.TempFileMixin):
    def setUp(self):
        """Make a valid python temp file."""
        lines = ["from __future__ import print_function",
                 "import sys",
                 "print('on stdout', end='', file=sys.stdout)",
                 "print('on stderr', end='', file=sys.stderr)",
                 "sys.stdout.flush()",
                 "sys.stderr.flush()"]
        self.mktmp('\n'.join(lines))

    def test_system(self):
        status = system('python "%s"' % self.fname)
        self.assertEquals(status, 0)

    def test_system_quotes(self):
        status = system('python -c "import sys"')
        self.assertEquals(status, 0)

    def test_getoutput(self):
        out = getoutput('python "%s"' % self.fname)
        self.assertEquals(out, 'on stdout')

    def test_getoutput_quoted(self):
        out = getoutput('python -c "print (1)"')
        self.assertEquals(out.strip(), '1')

    #Invalid quoting on windows
    @dec.skip_win32
    def test_getoutput_quoted2(self):
        out = getoutput("python -c 'print (1)'")
        self.assertEquals(out.strip(), '1')
        out = getoutput("python -c 'print (\"1\")'")
        self.assertEquals(out.strip(), '1')

    def test_getoutput(self):
        out, err = getoutputerror('python "%s"' % self.fname)
        self.assertEquals(out, 'on stdout')
        self.assertEquals(err, 'on stderr')
