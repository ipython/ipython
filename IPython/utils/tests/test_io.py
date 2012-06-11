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

import sys

from StringIO import StringIO
from subprocess import Popen, PIPE

import nose.tools as nt

from IPython.testing import decorators as dec
from IPython.utils.io import Tee, capture_output
from IPython.utils.py3compat import doctest_refactor_print

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


def test_tee_simple():
    "Very simple check with stdout only"
    chan = StringIO()
    text = 'Hello'
    tee = Tee(chan, channel='stdout')
    print >> chan, text
    nt.assert_equal(chan.getvalue(), text+"\n")


class TeeTestCase(dec.ParametricTestCase):

    def tchan(self, channel, check='close'):
        trap = StringIO()
        chan = StringIO()
        text = 'Hello'
        
        std_ori = getattr(sys, channel)
        setattr(sys, channel, trap)

        tee = Tee(chan, channel=channel)
        print >> chan, text,
        setattr(sys, channel, std_ori)
        trap_val = trap.getvalue()
        nt.assert_equals(chan.getvalue(), text)
        if check=='close':
            tee.close()
        else:
            del tee

    def test(self):
        for chan in ['stdout', 'stderr']:
            for check in ['close', 'del']:
                yield self.tchan(chan, check)

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
        print 'hi, stdout'
        print >> sys.stderr, 'hi, stderr'
    
    nt.assert_equals(io.stdout, 'hi, stdout\n')
    nt.assert_equals(io.stderr, 'hi, stderr\n')
