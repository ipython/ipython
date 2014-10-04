# encoding: utf-8
"""Tests for io.py"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function
from __future__ import absolute_import

import io as stdlib_io
import os.path
import stat
import sys

from subprocess import Popen, PIPE
import unittest

import nose.tools as nt

from IPython.testing.decorators import skipif
from IPython.utils.io import (Tee, capture_output, unicode_std_stream,
                              atomic_writing,
                              )
from IPython.utils.py3compat import doctest_refactor_print, PY3
from IPython.utils.tempdir import TemporaryDirectory

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


def test_tee_simple():
    "Very simple check with stdout only"
    chan = StringIO()
    text = 'Hello'
    tee = Tee(chan, channel='stdout')
    print(text, file=chan)
    nt.assert_equal(chan.getvalue(), text+"\n")


class TeeTestCase(unittest.TestCase):

    def tchan(self, channel, check='close'):
        trap = StringIO()
        chan = StringIO()
        text = 'Hello'
        
        std_ori = getattr(sys, channel)
        setattr(sys, channel, trap)

        tee = Tee(chan, channel=channel)
        print(text, end='', file=chan)
        setattr(sys, channel, std_ori)
        trap_val = trap.getvalue()
        nt.assert_equal(chan.getvalue(), text)
        if check=='close':
            tee.close()
        else:
            del tee

    def test(self):
        for chan in ['stdout', 'stderr']:
            for check in ['close', 'del']:
                self.tchan(chan, check)

def test_io_init():
    """Test that io.stdin/out/err exist at startup"""
    for name in ('stdin', 'stdout', 'stderr'):
        cmd = doctest_refactor_print("from IPython.utils import io;print io.%s.__class__"%name)
        p = Popen([sys.executable, '-c', cmd],
                    stdout=PIPE)
        p.wait()
        classname = p.stdout.read().strip().decode('ascii')
        # __class__ is a reference to the class object in Python 3, so we can't
        # just test for string equality.
        assert 'IPython.utils.io.IOStream' in classname, classname

def test_capture_output():
    """capture_output() context works"""
    
    with capture_output() as io:
        print('hi, stdout')
        print('hi, stderr', file=sys.stderr)
    
    nt.assert_equal(io.stdout, 'hi, stdout\n')
    nt.assert_equal(io.stderr, 'hi, stderr\n')

def test_UnicodeStdStream():
    # Test wrapping a bytes-level stdout
    if PY3:
        stdoutb = stdlib_io.BytesIO()
        stdout = stdlib_io.TextIOWrapper(stdoutb, encoding='ascii')
    else:
        stdout = stdoutb = stdlib_io.BytesIO()

    orig_stdout = sys.stdout
    sys.stdout = stdout
    try:
        sample = u"@łe¶ŧ←"
        unicode_std_stream().write(sample)

        output = stdoutb.getvalue().decode('utf-8')
        nt.assert_equal(output, sample)
        assert not stdout.closed
    finally:
        sys.stdout = orig_stdout

@skipif(not PY3, "Not applicable on Python 2")
def test_UnicodeStdStream_nowrap():
    # If we replace stdout with a StringIO, it shouldn't get wrapped.
    orig_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        nt.assert_is(unicode_std_stream(), sys.stdout)
        assert not sys.stdout.closed
    finally:
        sys.stdout = orig_stdout

def test_atomic_writing():
    class CustomExc(Exception): pass

    with TemporaryDirectory() as td:
        f1 = os.path.join(td, 'penguin')
        with stdlib_io.open(f1, 'w') as f:
            f.write(u'Before')
        
        if os.name != 'nt':
            os.chmod(f1, 0o701)
            orig_mode = stat.S_IMODE(os.stat(f1).st_mode)

        f2 = os.path.join(td, 'flamingo')
        try:
            os.symlink(f1, f2)
            have_symlink = True
        except (AttributeError, NotImplementedError, OSError):
            # AttributeError: Python doesn't support it
            # NotImplementedError: The system doesn't support it
            # OSError: The user lacks the privilege (Windows)
            have_symlink = False

        with nt.assert_raises(CustomExc):
            with atomic_writing(f1) as f:
                f.write(u'Failing write')
                raise CustomExc

        # Because of the exception, the file should not have been modified
        with stdlib_io.open(f1, 'r') as f:
            nt.assert_equal(f.read(), u'Before')

        with atomic_writing(f1) as f:
            f.write(u'Overwritten')

        with stdlib_io.open(f1, 'r') as f:
            nt.assert_equal(f.read(), u'Overwritten')

        if os.name != 'nt':
            mode = stat.S_IMODE(os.stat(f1).st_mode)
            nt.assert_equal(mode, orig_mode)

        if have_symlink:
            # Check that writing over a file preserves a symlink
            with atomic_writing(f2) as f:
                f.write(u'written from symlink')
            
            with stdlib_io.open(f1, 'r') as f:
                nt.assert_equal(f.read(), u'written from symlink')