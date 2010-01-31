# encoding: utf-8
"""Tests for io.py"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys

from cStringIO import StringIO

import nose.tools as nt

from IPython.testing import decorators as dec
from IPython.utils.io import Tee

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


def test_tee_simple():
    "Very simple check with stdout only"
    chan = StringIO()
    text = 'Hello'
    tee = Tee(chan, channel='stdout')
    print >> chan, text,
    nt.assert_equal(chan.getvalue(), text)


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
