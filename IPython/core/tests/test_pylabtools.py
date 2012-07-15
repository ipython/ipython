"""Tests for pylab tools module.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2011, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports

# Third-party imports
import matplotlib; matplotlib.use('Agg')
import nose.tools as nt

from matplotlib import pyplot as plt
import numpy as np

# Our own imports
from IPython.testing import decorators as dec
from .. import pylabtools as pt

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Local utilities
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

@dec.parametric
def test_figure_to_svg():
    # simple empty-figure test
    fig = plt.figure()
    yield nt.assert_equal(pt.print_figure(fig, 'svg'), None)

    plt.close('all')

    # simple check for at least svg-looking output
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,3])
    plt.draw()
    svg = pt.print_figure(fig, 'svg')[:100].lower()
    yield nt.assert_true('doctype svg' in svg)


def test_import_pylab():
    ip = get_ipython()
    ns = {}
    pt.import_pylab(ns, import_all=False)
    nt.assert_true('plt' in ns)
    nt.assert_equal(ns['np'], np)
