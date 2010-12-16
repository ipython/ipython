"""Tests for the IPython tab-completion machinery.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import os
import sys
import unittest

# third party
import nose.tools as nt

# our own packages
from IPython.utils.tempdir import TemporaryDirectory
from IPython.core.history import HistoryManager

def test_history():

    ip = get_ipython()
    with TemporaryDirectory() as tmpdir:
        #tmpdir = '/software/temp'
        histfile = os.path.realpath(os.path.join(tmpdir, 'history.json'))
        # Ensure that we restore the history management that we mess with in
        # this test doesn't affect the IPython instance used by the test suite
        # beyond this test.
        hist_manager_ori = ip.history_manager
        try:
            ip.history_manager = HistoryManager(ip)
            ip.history_manager.hist_file = histfile
            print 'test',histfile
            hist = ['a=1\n', 'def f():\n    test = 1\n    return test\n', 'b=2\n']
            # test save and load
            ip.history_manager.input_hist_raw[:] = []
            for h in hist:
                ip.history_manager.input_hist_raw.append(h)
            ip.save_history()
            ip.history_manager.input_hist_raw[:] = []
            ip.reload_history()
            print type(ip.history_manager.input_hist_raw)
            print ip.history_manager.input_hist_raw
            nt.assert_equal(len(ip.history_manager.input_hist_raw), len(hist))
            for i,h in enumerate(hist):
                nt.assert_equal(hist[i], ip.history_manager.input_hist_raw[i])
        finally:
            # Restore history manager
            ip.history_manager = hist_manager_ori
