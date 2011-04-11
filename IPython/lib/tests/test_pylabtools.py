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
    yield nt.assert_equal(pt.figure_to_svg(fig), None)

    plt.close('all')

    # simple check for at least svg-looking output
    fig, ax = plt.subplots()
    ax.plot([1,2,3])
    plt.draw()
    svg = pt.figure_to_svg(fig)[:100].lower()
    yield nt.assert_true('doctype svg' in svg)
