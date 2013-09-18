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

from IPython.kernel import launcher, connect
from IPython import kernel

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

def test_kms():
    for base in ("", "Multi"):
        KM = base + "KernelManager"
        nt.assert_in(KM, dir(kernel))

def test_kcs():
    for base in ("", "Blocking"):
        KM = base + "KernelClient"
        nt.assert_in(KM, dir(kernel))

def test_launcher():
    for name in launcher.__all__:
        nt.assert_in(name, dir(kernel))

def test_connect():
    for name in connect.__all__:
        nt.assert_in(name, dir(kernel))

