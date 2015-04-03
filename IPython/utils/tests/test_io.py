# encoding: utf-8
"""Tests for io.py"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
from __future__ import absolute_import

import io as stdlib_io
import os.path
import stat
import sys

from subprocess import Popen, PIPE
import unittest

import nose.tools as nt

from IPython.testing.decorators import skipif, skip_win32
from IPython.utils.io import Tee, capture_output
from IPython.utils.py3compat import doctest_refactor_print, PY3
from IPython.utils.tempdir import TemporaryDirectory

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO


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


