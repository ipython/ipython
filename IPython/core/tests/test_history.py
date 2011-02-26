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
from IPython.core.history import HistoryManager, extract_hist_ranges

def test_history():

    ip = get_ipython()
    with TemporaryDirectory() as tmpdir:
        #tmpdir = '/software/temp'
        histfile = os.path.realpath(os.path.join(tmpdir, 'history.sqlite'))
        # Ensure that we restore the history management that we mess with in
        # this test doesn't affect the IPython instance used by the test suite
        # beyond this test.
        hist_manager_ori = ip.history_manager
        try:
            ip.history_manager = HistoryManager(shell=ip)
            ip.history_manager.hist_file = histfile
            ip.history_manager.init_db()  # Has to be called after changing file
            print 'test',histfile
            hist = ['a=1', 'def f():\n    test = 1\n    return test', 'b=2']
            for i, h in enumerate(hist, start=1):
                ip.history_manager.store_inputs(i, h)
            
            nt.assert_equal(ip.history_manager.input_hist_raw, [''] + hist)
            
            # Check lines were written to DB
            c = ip.history_manager.db.execute("SELECT source_raw FROM history")
            nt.assert_equal([x for x, in c], hist)
              
            # New session
            ip.history_manager.reset()
            newcmds = ["z=5","class X(object):\n    pass", "k='p'"]
            for i, cmd in enumerate(newcmds):
                ip.history_manager.store_inputs(i, cmd)
            gothist = ip.history_manager.get_history(start=1, stop=4)
            nt.assert_equal(list(gothist), zip([0,0,0],[1,2,3], newcmds))
            # Previous session:
            gothist = ip.history_manager.get_history(-1, 1, 4)
            nt.assert_equal(list(gothist), zip([1,1,1],[1,2,3], hist))
            
            # Cross testing: check that magic %save can get previous session.
            testfilename = os.path.realpath(os.path.join(tmpdir, "test.py"))
            ip.magic_save(testfilename + " ~1/1-3")
            testfile = open(testfilename, "r")
            nt.assert_equal(testfile.read(), "\n".join(hist))
        finally:
            # Restore history manager
            ip.history_manager = hist_manager_ori

def test_extract_hist_ranges():
    instr = "1 2/3 ~4/5-6 ~4/7-~4/9 ~9/2-~7/5"
    expected = [(0, 1, 2),  # 0 == current session
                (2, 3, 4),
                (-4, 5, 7),
                (-4, 7, 10),
                (-9, 2, None),  # None == to end
                (-8, 1, None),
                (-7, 1, 6)]
    actual = list(extract_hist_ranges(instr))
    nt.assert_equal(actual, expected)
