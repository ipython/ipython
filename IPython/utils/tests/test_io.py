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
import sys

from subprocess import Popen, PIPE
import unittest

import nose.tools as nt

from IPython.testing.decorators import skipif
from IPython.utils.io import Tee, capture_output, unicode_std_stream
from IPython.utils.py3compat import doctest_refactor_print, PY3

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
    Tee(chan, channel='stdout')
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
        trap.getvalue()
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