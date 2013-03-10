"""Test the IPython.kernel public API

Authors
-------
* MinRK
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import nose.tools as nt

from IPython.testing import decorators as dec

from IPython.kernel import launcher, connect
from IPython import kernel

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

@dec.parametric
def test_kms():
    for base in ("", "Multi"):
        KM = base + "KernelManager"
        yield nt.assert_true(KM in dir(kernel), KM)

@dec.parametric
def test_kcs():
    for base in ("", "Blocking"):
        KM = base + "KernelClient"
        yield nt.assert_true(KM in dir(kernel), KM)

@dec.parametric
def test_launcher():
    for name in launcher.__all__:
        yield nt.assert_true(name in dir(kernel), name)

@dec.parametric
def test_connect():
    for name in connect.__all__:
        yield nt.assert_true(name in dir(kernel), name)

