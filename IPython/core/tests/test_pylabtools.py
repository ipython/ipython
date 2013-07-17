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
from IPython.core.interactiveshell import InteractiveShell
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

class TestPylabSwitch(object):
    class Shell(InteractiveShell):
        def enable_gui(self, gui):
            pass
    
    def setup(self):
        import matplotlib
        def act_mpl(backend):
            matplotlib.rcParams['backend'] = backend

        # Save rcParams since they get modified
        self._saved_rcParams = matplotlib.rcParams
        matplotlib.rcParams = dict(backend='Qt4Agg')

        # Mock out functions
        self._save_am = pt.activate_matplotlib
        pt.activate_matplotlib = act_mpl
        self._save_ip = pt.import_pylab
        pt.import_pylab = lambda *a,**kw:None
        self._save_cis = pt.configure_inline_support
        pt.configure_inline_support = lambda *a,**kw:None

    def teardown(self):
        pt.activate_matplotlib = self._save_am
        pt.import_pylab = self._save_ip
        pt.configure_inline_support = self._save_cis
        import matplotlib
        matplotlib.rcParams = self._saved_rcParams

    def test_qt(self):
        s = self.Shell()
        gui, backend = s.enable_matplotlib(None)
        nt.assert_equal(gui, 'qt')
        nt.assert_equal(s.pylab_gui_select, 'qt')

        gui, backend = s.enable_matplotlib('inline')
        nt.assert_equal(gui, 'inline')
        nt.assert_equal(s.pylab_gui_select, 'qt')

        gui, backend = s.enable_matplotlib('qt')
        nt.assert_equal(gui, 'qt')
        nt.assert_equal(s.pylab_gui_select, 'qt')

        gui, backend = s.enable_matplotlib('inline')
        nt.assert_equal(gui, 'inline')
        nt.assert_equal(s.pylab_gui_select, 'qt')

        gui, backend = s.enable_matplotlib()
        nt.assert_equal(gui, 'qt')
        nt.assert_equal(s.pylab_gui_select, 'qt')

    def test_inline(self):
        s = self.Shell()
        gui, backend = s.enable_matplotlib('inline')
        nt.assert_equal(gui, 'inline')
        nt.assert_equal(s.pylab_gui_select, None)

        gui, backend = s.enable_matplotlib('inline')
        nt.assert_equal(gui, 'inline')
        nt.assert_equal(s.pylab_gui_select, None)

        gui, backend = s.enable_matplotlib('qt')
        nt.assert_equal(gui, 'qt')
        nt.assert_equal(s.pylab_gui_select, 'qt')

    def test_qt_gtk(self):
        s = self.Shell()
        gui, backend = s.enable_matplotlib('qt')
        nt.assert_equal(gui, 'qt')
        nt.assert_equal(s.pylab_gui_select, 'qt')

        gui, backend = s.enable_matplotlib('gtk')
        nt.assert_equal(gui, 'qt')
        nt.assert_equal(s.pylab_gui_select, 'qt')

